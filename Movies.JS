const { MongoClient } = require('mongodb');
const { graphql, buildSchema } = require('graphql');

const uri = 'mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<dbname>?retryWrites=true&w=majority';

// Define the GraphQL schema
const schema = buildSchema(`
  type Movie {
    title: String
    year: Int
    imdb: String
  }

  type Query {
    movies: [Movie]
  }
`);

// Define the resolver functions
const resolvers = {
  Query: {
    movies: async () => {
      const client = new MongoClient(uri);
      await client.connect();
      const db = client.db('sample_mflix');
      const movies = await db.collection('movies').find().toArray();
      return movies;
    },
  },
};

// Define the GraphQL query
const query = `
  {
    movies {
      title
      year
      imdb
    }
  }
`;

// Execute the query using GraphQL
graphql(schema, query, resolvers)
  .then((result) => console.log(result))
  .catch((error) => console.error(error));
