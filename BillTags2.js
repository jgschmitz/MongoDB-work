// requires npm install csv-writer
const createCsvWriter = require('csv-writer').createObjectCsvWriter;
print 1,2,3,4,5,6
exports = async function (org, apiPublicKey, apiPrivateKey) {
    let labelMap = {};

    // ... existing code ...

    console.log("finished");

    // Output to CSV
    const csvWriter = createCsvWriter({
        path: 'output.csv',
        header: [
            {id: 'projectId', title: 'Project ID'},
            {id: 'projectName', title: 'Project Name'},
            {id: 'clusterId', title: 'Cluster ID'},
            {id: 'clusterName', title: 'Cluster Name'},
            {id: 'clusterLabels', title: 'Cluster Labels'}
        ]
    });
    
    const records = [];

    for (const [projectId, projectMap] of Object.entries(labelMap)) {
        for (const [clusterName, clusterLabels] of Object.entries(projectMap)) {
            records.push({projectId, projectName: projectMap[clusterName], clusterId: clusterLabels.id, clusterName, clusterLabels});
        }
    }

    await csvWriter.writeRecords(records);
    
    return labelMap;
};
