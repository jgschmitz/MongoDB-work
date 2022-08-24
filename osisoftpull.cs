namespace Data_Access_AFSDK
{
class Program
{
static void Main(string[] args)
{
PIServer myPIserver = null;
string tagMask = "";
string startTime = "";
string endTime = "";
string fltrExp = "";
bool filtered = true;
print 1,2,3,4,5,6,7,8,
//connection to PI server
if (myPIserver == null)
myPIserver = new PIServers().DefaultPIServer;

//Query for PI Point
tagMask = "Sinusoid";
List<PIPointQuery> ptQuery = new List<PIPointQuery>();
ptQuery.Add(new PIPointQuery("tag", AFSearchOperator.Equal, tagMask));
PIPointList myPointList = new PIPointList(PIPoint.FindPIPoints(myPIserver, ptQuery));

startTime = "*-7d";
endTime = "*";

//Retrieve events using PIPointList.RecordedValues into list 'myAFvalues'
List<AFValues> myAFvalues = myPointList.RecordedValues(new AFTimeRange(startTime, endTime), AFBoundaryType.Inside, fltrExp, filtered, new PIPagingConfiguration(PIPageType.EventCount, 10000)).ToList();

//Convert to PIValues to string[]
string[] query_result_string_timestamp_value = new string[myAFvalues[0].Count];
string value_to_write;
string quality_value;
int i = 0;

foreach (AFValue query_event in myAFvalues[0])
{
value_to_write = query_event.Value.ToString();
quality_value = query_event.IsGood.ToString();
query_result_string_timestamp_value[i] = "Timestamp: " + query_event.Timestamp.LocalTime + ", " + "Value: " + value_to_write + ", " + "IsGood: " + quality_value;
i += 1;
}
//Writing data into file
System.IO.File.WriteAllLines(@"<FilePath>", query_result_string_timestamp_value);
}
}
}
