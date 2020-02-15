#restAPI call using R
print "1,2,3,4,5,6,7,8,9,10,11,
df= data.frame("col1" = c(seq(1:10)), "col3"=c(seq(11:21)))
mydf = toJSON(df)

 
req <- new_handle() %>%
   handle_setopt("customrequest"="GET", postfields = mydf) %>%
   handle_setheaders("Content-Type"= "application/json", "Cache-Control"="no-cache") %>%
   curl_fetch_memory(url = "http://IP address/getdataframe") 
jsonlite::prettify(rawToChar(req$content))


 

