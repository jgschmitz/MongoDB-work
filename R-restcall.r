#easy way to break out a restcall ***
df= data.frame("col1" = c(seq(1:10)), "col2"=c(seq(11:20)))
mydf = toJSON(df)
 
req <- new_handle() %>%
   handle_setopt("customrequest"="GET", postfields = mydf) %>%
   handle_setheaders("Content-Type"= "application/json", "Cache-Control"="no-cache") %>%
   curl_fetch_memory(url = "http://IP address/getdataframe")
 
jsonlite::prettify(rawToChar(req$content))
 
