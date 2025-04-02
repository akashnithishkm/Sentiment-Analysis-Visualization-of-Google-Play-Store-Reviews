import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from google_play_scraper import Sort, reviews
from datetime import datetime, timedelta
from textblob import TextBlob
from wordcloud import WordCloud
import seaborn as sns

# Function to get reviews from the last 3 months
def get_reviews_last_3_months(app_id, lang='en', country='in', count=200):
    all_reviews = []
    continuation_token = None
    seen_ids = set()  # Set to track unique review IDs
    three_months_ago = datetime.now() - timedelta(days=90)  # Calculate date for 3 months ago

    while True:
        print(f"Fetching reviews... Continuation Token: {continuation_token}")
        try:
            result, continuation_token = reviews(
                app_id,
                lang=lang,
                country=country,
                sort=Sort.NEWEST,
                count=count,
                continuation_token=continuation_token
            )
            new_reviews = [review for review in result if review['reviewId'] not in seen_ids]  # Filter new reviews
            print(f"Fetched {len(new_reviews)} new reviews.")
            
            # Stop fetching reviews if they are older than 3 months
            for review in new_reviews:
                review_date = review['at']
                if review_date < three_months_ago:
                    print("Stopping loop: Review date is older than 3 months.")
                    return all_reviews

                all_reviews.append(review)
                seen_ids.add(review['reviewId'])

            if not continuation_token:
                print("Stopping loop: No more reviews available.")
                break
        except Exception as e:
            print(f"Error fetching reviews: {e}")
            break

    return all_reviews

# Set app ID for the app you choose
app_id = 'in.swiggy.android'

# Get reviews from the last 3 months
reviews_last_3_months = get_reviews_last_3_months(app_id)

# Convert reviews to DataFrame
df = pd.DataFrame(reviews_last_3_months)

# Check if 'at' column exists and convert review date to datetime
if 'at' in df.columns:
    df['date'] = pd.to_datetime(df['at'])

# Sort the DataFrame by date in descending order (most recent first)
df_last_three_months = df.sort_values(by='date', ascending=False)

# Print the count of reviews in the last 3 months
print(f"Total reviews in the last 3 months: {len(df_last_three_months)}")

# Save the filtered and sorted DataFrame to an Excel file
df_last_three_months.to_excel(f"{app_id}_reviews_last_3_months.xlsx", index=False)

print("The file has been downloaded.")

# Create a PDF to save all visualizations
pdf_filename = f"{app_id}_reviews_visualizations.pdf"
with PdfPages(pdf_filename) as pdf:

    # 1. Review Trend Over Time
    review_counts = df_last_three_months.groupby(df['date'].dt.date).size()
    plt.figure(figsize=(12, 6))
    sns.lineplot(x=review_counts.index, y=review_counts.values, marker='o', color='blue')
    plt.title('Review Trend Over Time (Last 3 Months)')
    plt.xlabel('Date')
    plt.ylabel('Number of Reviews')
    plt.xticks(rotation=45)
    plt.grid()
    plt.tight_layout()
    pdf.savefig()
    plt.close()

    # 2. Distribution of Ratings
    plt.figure(figsize=(10, 5))
    sns.histplot(df_last_three_months['score'], bins=5, color='lightgreen', kde=True)
    plt.title('Distribution of Review Ratings')
    plt.xlabel('Rating')
    plt.ylabel('Number of Reviews')
    plt.xticks(range(1, 6))
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    pdf.savefig()
    plt.close()

    # 3. Word Cloud of Review Content (remains unchanged)
    all_text = ' '.join(df_last_three_months['content'])
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Word Cloud of Reviews')
    pdf.savefig()
    plt.close()

    # 4. Sentiment Distribution of Reviews
    df_last_three_months['sentiment'] = df_last_three_months['content'].apply(lambda x: TextBlob(x).sentiment.polarity)
    plt.figure(figsize=(10, 5))
    sns.histplot(df_last_three_months['sentiment'], bins=30, color='purple', kde=True)
    plt.title('Sentiment Distribution of Reviews')
    plt.xlabel('Sentiment Score')
    plt.ylabel('Number of Reviews')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    pdf.savefig()
    plt.close()

    # 5. Positive vs. Negative Reviews
    df_last_three_months['review_type'] = df_last_three_months['score'].apply(lambda x: 'Positive' if x >= 4 else 'Negative')
    plt.figure(figsize=(8, 5))
    sns.countplot(x='review_type', data=df_last_three_months, hue='review_type', palette=['green', 'red'], legend=False)
    plt.title('Positive vs. Negative Reviews')
    plt.xlabel('Review Type')
    plt.ylabel('Number of Reviews')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    pdf.savefig()
    plt.close()

print(f"The visualizations have been saved to {pdf_filename}.")
