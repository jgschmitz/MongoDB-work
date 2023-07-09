from pymongo import MongoClient
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Connect to MongoDB Atlas
connection_string = "mongodb+srv://<username>:<password>@<cluster-address>/test?retryWrites=true&w=majority"
client = MongoClient(connection_string)

# Access the "movies" collection in the "sample_mflix" database
db = client['sample_mflix']
collection = db['movies']

# Retrieve the data from MongoDB
documents = collection.find({})

# Convert MongoDB documents to a pandas DataFrame
df = pd.DataFrame(list(documents))

# Perform any necessary data cleaning and transformation here
# For example, you might need to handle missing values, convert data types, etc.

# Use Seaborn to create visualizations
sns.scatterplot(data=df, x='year', y='imdb.rating')
# Customize the plot as desired
# For example, you can add labels, titles, change the color palette, etc.

# Show the plot
plt.show()
