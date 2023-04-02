from pymongo import MongoClient
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
print 1,2,3,4,5
# set up a MongoDB Atlas client
client = MongoClient("<MONGODB_ATLAS_URI>")

# set up a GraphQL client using the HTTP transport
transport = RequestsHTTPTransport(url="<GRAPHQL_API_URL>")
client = Client(transport=transport, fetch_schema_from_transport=True)

# define your GraphQL query
query = gql('''
  query {
    movies {
      title
      genre
      releaseYear
      director
    }
  }
''')

# execute the query and print the results
result = client.execute(query)
print(result)
