import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from google_play_scraper import Sort, reviews
from datetime import datetime, timedelta
from textblob import TextBlob
from wordcloud import WordCloud
import seaborn as sns

# Define categories and apps
apps = {
    "📱 Social Media & Communication": "com.instagram.android",
    "🎵 Music & Video Streaming": "com.spotify.music",
    "🛍 Shopping & E-commerce": "com.amazon.mShop.android.shopping",
    "🚕 Travel & Transport": "com.ubercab",
    "🏋️‍♂️ Health & Fitness": "com.myfitnesspal.android",
    "🎮 Gaming": "com.supercell.clashofclans",
    "📚 Education": "com.duolingo",
    "📷 Photography": "com.adobe.lrmobile",
    "💰 Finance": "com.phonepe.app",
    "🍔 Food & Delivery": "in.swiggy.android"
}

# Set time range for the last 30 days
thirty_days_ago = datetime.now() - timedelta(days=30)

def get_reviews(app_id, count=200):
    """Fetches reviews from the last 30 days."""
    all_reviews = []
    continuation_token = None
    seen_ids = set()

    while True:
        try:
            result, continuation_token = reviews(
                app_id, lang='en', country='in', sort=Sort.NEWEST, count=count,
                continuation_token=continuation_token
            )
            new_reviews = [r for r in result if r['reviewId'] not in seen_ids]
            
            # Stop fetching if reviews are older than 30 days
            for review in new_reviews:
                if review['at'] < thirty_days_ago:
                    print(f"[STOPPED] Older reviews detected for {app_id}.")
                    return all_reviews
                
                all_reviews.append(review)
                seen_ids.add(review['reviewId'])
            
            print(f"[FETCHED] {len(new_reviews)} reviews for {app_id}.")
            if not continuation_token:
                break
        except Exception as e:
            print(f"[ERROR] Could not fetch reviews for {app_id}: {e}")
            break
    return all_reviews

# Process each app
for category, app_id in apps.items():
    print(f"\n📌 Fetching reviews for {category} ({app_id})...\n")
    reviews_data = get_reviews(app_id)
    df = pd.DataFrame(reviews_data)
    
    if df.empty:
        print(f"[INFO] No recent reviews found for {app_id}. Skipping...")
        continue
    
    df['date'] = pd.to_datetime(df['at'])
    df_sorted = df.sort_values(by='date', ascending=False)
    
    excel_filename = f"{app_id}_reviews_last_30_days.xlsx"
    df_sorted.to_excel(excel_filename, index=False)
    print(f"✅ Saved {len(df_sorted)} reviews to {excel_filename}")

    # PDF for visualizations
    pdf_filename = f"{app_id}_reviews_visualizations.pdf"
    with PdfPages(pdf_filename) as pdf:
        # 1. Review Trend Over Time
        plt.figure(figsize=(12, 6))
        review_counts = df_sorted.groupby(df_sorted['date'].dt.date).size()
        sns.lineplot(x=review_counts.index, y=review_counts.values, marker='o', color='blue')
        plt.title('Review Trend Over Last 30 Days')
        plt.xlabel('Date')
        plt.ylabel('Number of Reviews')
        plt.xticks(rotation=45)
        plt.grid()
        plt.tight_layout()
        pdf.savefig()
        plt.close()
        
        # 2. Distribution of Ratings
        plt.figure(figsize=(10, 5))
        sns.histplot(df_sorted['score'], bins=5, color='lightgreen', kde=True)
        plt.title('Distribution of Review Ratings')
        plt.xlabel('Rating')
        plt.ylabel('Number of Reviews')
        plt.xticks(range(1, 6))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        pdf.savefig()
        plt.close()
        
        # 3. Word Cloud of Review Content
        all_text = ' '.join(df_sorted['content'].dropna())
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_text)
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('Word Cloud of Reviews')
        pdf.savefig()
        plt.close()
        
        # 4. Sentiment Distribution of Reviews
        df_sorted['sentiment'] = df_sorted['content'].fillna('').apply(lambda x: TextBlob(x).sentiment.polarity)
        plt.figure(figsize=(10, 5))
        sns.histplot(df_sorted['sentiment'], bins=30, color='purple', kde=True)
        plt.title('Sentiment Distribution of Reviews')
        plt.xlabel('Sentiment Score')
        plt.ylabel('Number of Reviews')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        pdf.savefig()
        plt.close()
        
        # 5. Positive vs. Negative Reviews
        df_sorted['review_type'] = df_sorted['score'].apply(lambda x: 'Positive' if x >= 4 else 'Negative')
        plt.figure(figsize=(8, 5))
        sns.countplot(x='review_type', data=df_sorted, hue='review_type', palette=['green', 'red'], legend=False)
        plt.title('Positive vs. Negative Reviews')
        plt.xlabel('Review Type')
        plt.ylabel('Number of Reviews')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        pdf.savefig()
        plt.close()
    
    print(f"📄 Visualizations saved to {pdf_filename}\n")

print("✅ All apps processed successfully!")
