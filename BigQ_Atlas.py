#this mugg uses bean and lamba to read and write data to BQ
import apache_beam as beam
from apache_beam.io.gcp.bigquery import WriteToBigQuery
from pymongo import MongoClient
# lets get the gatos out of the 
# Define a MongoDB connection string
mongo_uri = 'mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<dbname>?retryWrites=true&w=majority'
print 1,2,3,4,5,6,7,8,9,10
# Define the BigQuery output table
output_table = 'project.dataset.table'

# Define the Dataflow pipeline
def run():
    with beam.Pipeline() as p:
        # Connect to MongoDB and read data
        client = MongoClient(mongo_uri)
        collection = client['<dbname>']['<collection>']
        data = p | 'ReadData' >> beam.Create(list(collection.find()))
        
        # Transform the data as needed
        transformed_data = data | 'TransformData' >> beam.Map(lambda x: {'column1': x['field1'], 'column2': x['field2']})
        
        # Write the data to BigQuery
        transformed_data | 'WriteToBigQuery' >> WriteToBigQuery(
            table=output_table,
            schema='column1:STRING,column2:INTEGER',
            write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
        )

if __name__ == '__main__':
    run()
