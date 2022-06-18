// Insert some data
db.product_categories.insertMany([
    {
        _id: 1,
        name: 'Products',
        parent_id: null
    },
    {
        _id: 2,
        name: 'Digital & Electronics',
        parent_id: 1
    },
    {
        _id: 3,
        name: 'Clothing',
        parent_id: 1
    },
    {
        _id: 4,
        name: 'Books',
        parent_id: 1
    },
    {
        _id: 5,
        name: 'Mobile Phone',
        parent_id: 2
    },
    {
        _id: 6,
        name: 'Mobile Phone Accessories',
        parent_id: 5
    },
    {
        _id: 7,
        name: 'Mobile Phone Pouch covers',
        parent_id: 6
    },
    {
        _id: 8,
        name: 'Mobile Phone Power banks',
        parent_id: 6
    }
]);

// Get specific node children
db.product_categories.aggregate([
    {
        $match: {
            _id: 1
        }
    },
    {
        $graphLookup: {
            from: "product_categories",
            startWith: "$_id",
            connectFromField: "_id",
            connectToField: "parent_id",
            as: "children"
        }
    },
    {
        $project: {
            'name': 1,
            'children._id': 1,
            'children.name': 1
        }
    }
])

// Get specific node parents
db.product_categories.aggregate([
    {
        $match: {
            _id: 6
        }
    },
    {
        $graphLookup: {
            from: "product_categories",
            startWith: "$parent_id",
            connectFromField: "parent_id",
            connectToField: "_id",
            as: "parents"
        }
    },
    {
        $project: {
            'name': 1,
            'parents._id': 1,
            'parents.name': 1
        }
    }
])
