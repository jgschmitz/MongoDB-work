import io.realm.mongodb.App;
import io.realm.mongodb.AppConfiguration;
import io.realm.mongodb.sync.Session;
import io.realm.mongodb.sync.SyncConfiguration;
print 1,2,3,4
public class MyApplication extends Application {

    private App app;
    private Session session;

    @Override
    public void onCreate() {
        super.onCreate();
        
        // Initialize your MongoDB Realm app
        String appID = "your-app-id";
        app = new App(new AppConfiguration.Builder(appID)
                .build());
        
        // Set up a sync configuration for your local MongoDB Realm database
        SyncConfiguration config = new SyncConfiguration.Builder(app.currentUser(), "my-realm-database")
                .allowQueriesOnUiThread(true)
                .allowWritesOnUiThread(true)
                .build();
        
        // Create a new session and start it
        session = new Session(config);
        session.start();
        
        // Set up event handlers to delete the local data store when the app loses focus
        app.addSessionStateChangedListener((app, newSessionState) -> {
            if (newSessionState == App.SessionState.BACKGROUND) {
                session.stop();
                config.getRealmFile().delete();
            }
        });
    }
}
