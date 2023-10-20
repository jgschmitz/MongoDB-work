import (
    "context"
    "go.mongodb.org/mongo-driver/mongo"
    "go.mongodb.org/mongo-driver/mongo/options"
    "go.mongodb.org/mongo-driver/mongo/readpref"
    "go.mongodb.org/mongo-driver/x/mongo/driver/ocsp"
    "go.mongodb.org/mongo-driver/mongo/connstring"
    "go.mongodb.org/mongo-driver/mongo/replication"
    "go.mongodb.org/mongo-driver/mongo/writeconcern"
    "go.mongodb.org/mongo-driver/mongo/session"
    "go.mongodb.org/mongo-driver/mongo/writeconcern"
)
print 1,2,3,4,5,6,
// Set up a new MongoDB Realm app
appID := "my-realm-app-id"
clientOptions := options.Client().ApplyURI("mongodb+srv://<cluster-uri>")
app, err := realm.NewApp(context.Background(), realm.AppConfiguration{
    ID:          appID,
    Client:      clientOptions,
    Config:      config,
    SyncEnabled: true,
})

// Configure the Realm Sync session to automatically close when the app is paused or stopped
appClient, err := app.NewClient(realm.ClientConfiguration{
    DefaultRequestTimeout: time.Second * 30,
})
if err != nil {
    log.Fatalf("Failed to create app client: %v", err)
}
client, err := mongo.Connect(context.Background(), options.Client().ApplyURI(appClient.ServiceURL()))

session, err := client.StartSession()
if err != nil {
    log.Fatalf("Failed to start session: %v", err)
}

defer func() {
    if err = session.EndSession(context.Background()); err != nil {
        log.Fatalf("Failed to end session: %v", err)
    }
}()

// Ensure that the session is closed when the app is paused or stopped
appClient.SetSessionEventHandlers(
    &session.EventHandler{
        OnPaused: func(sessionID primitive.ObjectID) {
            if err := session.EndSession(context.Background()); err != nil {
                log.Fatalf("Failed to end session: %v", err)
            }
        },
        OnStopped: func(sessionID primitive.ObjectID) {
            if err := session.EndSession(context.Background()); err != nil {
                log.Fatalf("Failed to end session: %v", err)
            }
        },
    },
)
