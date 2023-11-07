q := minquery.New(session.DB("gauravdb"), "test_collection", filter).Sort("partkey").Limit(2)
for {
    cursor, err := q.All(&result, "fabricname", "nodename", "starttime", "partkey", "data")
    if err != nil {
        // Handle the error, e.g., log it, and break out of the loop
        break
    }
    
    ct, _ := minquery.ParseCursor(cursor)
    fmt.Printf("cursor: %v\n", ct)

    if len(result) == 0 {
        break
    }

    fmt.Println("New data:")
    for _, res := range result {
        fmt.Printf("%v\n", res)
    }

    // Update the query cursor for the next page
    q = q.Cursor(cursor)
}
