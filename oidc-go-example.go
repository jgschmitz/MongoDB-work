package main

import (
    "context"
    "fmt"
    "log"
    "os"
    "time"

    "github.com/golang-jwt/jwt/v5"
    "github.com/mongodb/mongo-go-driver/mongo"
    "github.com/mongodb/mongo-go-driver/mongo/options"
    "github.com/sirupsen/logrus"
)

// MongoDB OIDC Configuration
const (
    MongoDBURI = "mongodb+srv://<your-cluster-url>" // Replace with your MongoDB Atlas cluster URL
    OIDCIssuer = "https://<your-oidc-provider>.auth0.com/" // Replace with your OIDC provider URL
    ClientID   = "<your-client-id>"                   // Replace with your OIDC client ID
)

// Custom Claims for JWT
type CustomClaims struct {
    Email string `json:"email"`
    jwt.RegisteredClaims
}

func main() {
    // Initialize logger
    logger := logrus.New()
    logger.SetLevel(logrus.DebugLevel)

    // Create a JWT token (this would typically come from your OIDC provider)
    claims := CustomClaims{
        Email: "user@example.com",
        RegisteredClaims: jwt.RegisteredClaims{
            Issuer:    OIDCIssuer,
            Audience:  jwt.ClaimStrings{ClientID},
            ExpiresAt: jwt.NewNumericDate(time.Now().Add(24 * time.Hour)),
            NotBefore: jwt.NewNumericDate(time.Now()),
            IssuedAt:  jwt.NewNumericDate(time.Now()),
        },
    }

    // Create JWT token
    token := jwt.NewWithClaims(jwt.SigningMethodRS256, claims)
    signedToken, err := token.SignedString([]byte("your-secret-key"))
    if err != nil {
        logger.Fatal(err)
    }

    // Create MongoDB client options with OIDC authentication
    clientOptions := options.Client().ApplyURI(MongoDBURI)
    
    // Set OIDC credentials
    clientOptions.SetAuth(options.Credential{
        AuthMechanism: "MONGODB-OIDC",
        Username:     "oidc",
        Password:     signedToken,
    })

    // Connect to MongoDB
    client, err := mongo.Connect(context.Background(), clientOptions)
    if err != nil {
        logger.Fatal(err)
    }
    defer client.Disconnect(context.Background())

    // Test the connection
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    if err := client.Ping(ctx, nil); err != nil {
        logger.Fatal(err)
    }

    // Use the database
    db := client.Database("test")
    collection := db.Collection("users")

    // Insert a test document
    insertResult, err := collection.InsertOne(ctx, map[string]interface{}{
        "name":  "Test User",
        "email": claims.Email,
    })
    if err != nil {
        logger.Fatal(err)
    }

    logger.Infof("Document inserted with ID: %v", insertResult.InsertedID)

    // Find the document
    var result map[string]interface{}
    if err := collection.FindOne(ctx, map[string]interface{}{"email": claims.Email}).Decode(&result); err != nil {
        logger.Fatal(err)
    }

    logger.Infof("Found document: %v", result)

    fmt.Println("OIDC authentication successful!")
}
