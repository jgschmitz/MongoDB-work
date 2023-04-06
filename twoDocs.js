const { MongoClient } = require('mongodb');

const uri = 'mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>?retryWrites=true&w=majority';

const client = new MongoClient(uri, { useNewUrlParser: true, useUnifiedTopology: true });

async function getOrdersWithCustomers() {
  await client.connect();
  const orders = client.db().collection('orders');
  const customers = client.db().collection('customers');
  const result = await orders.aggregate([
    {
      $lookup: {
        from: 'customers',
        localField: 'customerId',
        foreignField: '_id',
        as: 'customer'
      }
    },
    {
      $unwind: '$customer'
    }
  ]).toArray();
  await client.close();
  return result;
}

getOrdersWithCustomers().then(result => {
  console.log(result);
}).catch(err => {
  console.error(err);
});
