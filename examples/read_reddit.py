import kabigon

url = "https://reddit.com/r/confession/comments/1q1mzej/im_a_developer_for_a_major_food_delivery_app_the/"

# For Reddit posts, use HttpxLoader or PlaywrightLoader
loader = kabigon.Compose(
    [
        kabigon.HttpxLoader(),
        kabigon.PlaywrightLoader(),
    ]
)

# Load the content
content = loader.load_sync(url)
print(content)
