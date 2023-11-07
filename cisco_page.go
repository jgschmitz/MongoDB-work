q := minquery.New(session.DB("gauravdb"), "test_collection", filter).Sort("partkey").Limit(2)
for {
    cursor, err := q.All(&result, "fabricname", "nodename", "starttime", "partkey", "data")
    if err != nil {
        // error handle then out of loop
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

    // next page new cursor
    q = q.Cursor(cursor)
}
