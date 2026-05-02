from kabigon.loaders import RedditLoader

url = "https://reddit.com/r/confession/comments/1q1mzej/im_a_developer_for_a_major_food_delivery_app_the/"

# For Reddit posts, use the source-specific loader so the JSON/RSS fallbacks
# can avoid generic verification pages.
loader = RedditLoader()

# Load the content
content = loader.load_sync(url)
print(content)
