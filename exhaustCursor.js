#include <mongocxx/client.hpp>
#include <mongocxx/instance.hpp>

int main(int, char**) {
    mongocxx::instance inst{};
    mongocxx::client conn{mongocxx::uri{}};

    auto db = conn["test"];
    auto coll = db["collection"];

    mongocxx::pipeline pipeline = ...; // specify the pipeline for the aggregation operation
    mongocxx::options::aggregate options;
    options.cursor(mongocxx::cursor{});

    auto cursor = coll.aggregate(pipeline, options);
    mongocxx::cursor mongodb_cursor{cursor};
    mongocxx::database db = conn["test"];
    mongocxx::collection coll = db["collection"];

    auto cursor = coll.aggregate(pipeline, options);
    mongocxx::cursor mongodb_cursor{cursor};

    for (auto&& doc : mongodb_cursor) {
        // process each document
    }

    return 0;
}
