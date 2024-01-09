const createCsvWriter = require('csv-writer').createObjectCsvWriter;
print
exports = async function (org, apiPublicKey, apiPrivateKey) {
  const http_args = {
    "scheme": "https",
    "host": "cloud.mongodb.com",
    "username": apiPublicKey,
    "password": apiPrivateKey,
    "digestAuth": true,
    "path": `/api/atlas/v1.0/orgs/${org}/invoices/pending`
  };

  const response = await context.http.get(http_args);
  if (response.statusCode !== 200) {
    throw { "error": JSON.parse(response.body.text()).detail, "fn": "getInvoice", "statusCode": response.statusCode };
  }

  const body = JSON.parse(response.body.text());
  const labelMap = await context.functions.execute("getClusterTags", org, apiPublicKey, apiPrivateKey);
  const lineItems = body.lineItems.map(lineItem => {
    const labels = labelMap[lineItem.groupId]?.[lineItem.clusterName];
    lineItem.labels = labels ? JSON.stringify(labels) : "";
    return lineItem;
  });

  const csvWriter = createCsvWriter({
    path: 'output.csv',
    header: [
      { id: 'clusterName', title: 'Cluster Name' },
      { id: 'groupId', title: 'Group ID' },
      { id: 'invoiceId', title: 'Invoice ID' },
      { id: 'lineItemId', title: 'Line Item ID' },
      { id: 'product', title: 'Product' },
      { id: 'startDate', title: 'Start Date' },
      { id: 'endDate', title: 'End Date' },
      { id: 'amount', title: 'Amount' },
      { id: 'currency', title: 'Currency' },
      { id: 'labels', title: 'Labels' },
    ]
  });

  await csvWriter.writeRecords(lineItems);
  console.log("finished");
};
