const { ApolloServer } = require('apollo-server');
const { buildFederatedSchema } = require('@apollo/federation');
const { makeExecutableSchema } = require('graphql-tools');

// Define the first schema
const usersSchema = makeExecutableSchema({
  typeDefs: `
    type User @key(fields: "id") {
      id: ID!
      name: String!
      email: String!
    }

    type Query {
      user(id: ID!): User
    }
  `,
  resolvers: {
    Query: {
      user: (parent, { id }, context, info) => {
        // Code to fetch user data
      }
    }
  }
});

// Define the second schema
const productsSchema = makeExecutableSchema({
  typeDefs: `
    type Product @key(fields: "id") {
      id: ID!
      name: String!
      price: Float!
    }

    type Query {
      product(id: ID!): Product
    }
  `,
  resolvers: {
    Query: {
      product: (parent, { id }, context, info) => {
        // Code to fetch product data
      }
    }
  }
});

// Merge the schemas using Apollo Federation
const schema = buildFederatedSchema([
  { schema: usersSchema, resolvers: {} },
  { schema: productsSchema, resolvers: {} }
]);

// Create the Apollo Server
const server = new ApolloServer({
  schema,
  context: ({ req }) => {
    // Code to set up context object
  }
});

// Start the server
server.listen().then(({ url }) => {
  console.log(`🚀 Server ready at ${url}`);
});
