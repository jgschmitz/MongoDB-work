exports = async function(changeEvent) {
  let fullDocument = changeEvent.fullDocument;
  console.log(`Version: ${getContextValue("software_version")}`);

  if (changeEvent.operationType === "insert") {
    if (fullDocument.is_deleted || fullDocument.deleted_date){
      console.log(`A 'deleted' address added, no action needed. (ID - ${fullDocument._source.address_id})`);
      return;
    }
    enrichAndPublishAddress("add", transformAddress(fullDocument));
    return;
  } else if (["replace", "update"].includes(changeEvent.operationType)) {
    if (fullDocument.is_deleted || fullDocument.deleted_date) {
      enrichAndPublishAddress("delete", transformAddress(fullDocument));
      return;
    } else {
      enrichAndPublishAddress("update", transformAddress(fullDocument));
      return;
    }
  } else {
    const err_msg = "Unexpected database action detected. Document was not copied over.";
    insertErrorDocument(transformAddress(fullDocument), changeEvent.operationType, err_msg);
    console.error(err_msg);
    return;
  }
};

/**
 * Function for transofming incoming address document.
 * In Elasticsearch `_id` must be the same as the `_source.datasource_id`,
 * also all historical fields must be grouped together into `_history` section.
 *
 * @param {object} addressDocument The address document for transformation.
 * @returns {object}
 */
function transformAddress(addressDocument) {
  addressDocument._id = addressDocument._source.datasource_id;

  const {
    _id: documentId,
    _source: finalDocument,
    created_date: createdDate,
    modified_date: modifiedDate,
    deleted_date: deletedDate,
    datasource_file: datasourceFile
  } = addressDocument;

  const history = {
    created_date: createdDate,
    modified_date: modifiedDate,
    datasource_file: datasourceFile
  };
  finalDocument.history = history;
  
  // addressDocument may not contains a key `alternate_datasource_id` 
  if ('alternate_datasource_id' in addressDocument) {
    alt_datasource_id = addressDocument.alternate_datasource_id;
    finalDocument.alternate_datasource_id = alt_datasource_id;
  };

  return finalDocument;
}

/**
 * Makes final pub/sub message and publish it.
 *
 * @param {string} action An action to be performed on the address
 * @param {object} address The address document.
 * @returns {void}
 */
async function enrichAndPublishAddress(action, address) {
  let message = JSON.stringify({action: action, address_document: address});
  try {
    let resp = await publishToPubSub(message);
    if (resp.statusCode === 200) {
      console.log(`Address with id: '${address.address_id}' was published successfully! ${resp.body.text()}`);
    } else {
      let err_msg = `Pub/Sub error: ${JSON.parse(resp.body.text()).error.message}`;
      insertErrorDocument(address, action, err_msg, resp.statusCode);
      console.error(`${err_msg}`);
    }
  } catch (err) {
    let err_msg = `Unexpected error was occurred. ${err}`;
    insertErrorDocument(address, action, err_msg);
    console.error(`${err_msg}`);
  }
  return;
}

/**
 * Retrieves a value from context values by name.
 *
 * @param {string} key The name of the value to retrieve.
 * @returns {string}
 * @returns {object}
 */
function getContextValue(key) {
    const value = context.values.get(key);
    if (!value) {
        throw new Error(`Cannot fetch value ${key} from context.`);
    }
    return value;
}

/**
 * Writes to the collection of errors a document with a detailed description of the error.
 * @param {object} address The address document.
 * @param {string} action An action to be performed on the address.
 * @param {string} error_message  An error details.
 * @param error_code An error code.
 */
function insertErrorDocument(address, action, error_message, error_code=null) {
  const mongodb = context.services.get("mongodb-atlas");
  const db = mongodb.db("kw-addresses");
  const err_coll = getContextValue("realm_errors_collection");
  const created_date = new Date().toISOString().replace(/T/, ' ').replace(/\..+/, '');

  try {
    db.collection(err_coll).insertOne({
      address_id: address.address_id,
      address_document: address,
      created_date: created_date,
      action: action,
      error_code: error_code,
      error_message: error_message,
      is_processed: false,
      reprocessed_date: null});
  } catch (err) {
    console.error(`An error occurred while trying to write to the '${err_coll}'collection. Error message: ${err.message}`);
  }
  return;
}

/**
 * Publishes a message to a Pub/Sub topic via http request for reprocessing.
 * @param {string} message The message to publishing.
 * @returns {object} A response object.
 */
async function publishToPubSub(message) {
  const topicName = getContextValue('pub_sub_topic_name');

  const response = await context.http.post({
      url: `https://pubsub.googleapis.com/v1/${topicName}:publish`,
      body: {messages: [{"data": Buffer.from(message).toString('base64')}]},
      encodeBodyAsJSON: true,
      headers: {
        "Authorization": [`Bearer ${await getAccessToken()}`],
        "Content-Type": ["application/json"]
      }
    });
  return response;
}

/**
 * Gets a valid access token from the 'token' collection.
 * @returns {string} The access token.
 */
async function getAccessToken() {
  const mongodb = context.services.get("mongodb-atlas");
  const db = mongodb.db("kw-addresses");
  const collection = db.collection("token");

  try {
    const token = await collection.findOne({"type": "pubsub"});
    return token.access_token;
  } catch (err) {
    console.err(`Failed to get an access token: ${err}`);
  }
}
