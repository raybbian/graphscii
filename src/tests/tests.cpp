#include <catch2/catch_test_macros.hpp>
#include <boost/graph/graphviz.hpp>

#include "../simple_graph.hpp"
#include "../planarization_processor.hpp"
#include "../component_processor.hpp"

TEST_CASE("generate dfs spanning tree") {
    SimpleGraph input(5);
    boost::add_edge(0, 1, input);
    boost::add_edge(0, 2, input);
    boost::add_edge(1, 2, input);
    boost::add_edge(2, 3, input);
    boost::add_edge(2, 4, input);
    boost::add_edge(3, 4, input);
    PlanarizationProcessor pp(input);
    pp.generate_dfs_spanning_tree();
    REQUIRE(boost::num_edges(pp.dfs_spanning_tree) == 4);
    REQUIRE(boost::edge(0, 1, pp.dfs_spanning_tree).second);
    REQUIRE(boost::edge(1, 2, pp.dfs_spanning_tree).second);
    REQUIRE(boost::edge(2, 3, pp.dfs_spanning_tree).second);
    REQUIRE(boost::edge(3, 4, pp.dfs_spanning_tree).second);
    boost::write_graphviz(std::cout, pp.dfs_spanning_tree);
}

TEST_CASE("throw on planarization of non-connected-graph") {
    SimpleGraph input;
    boost::add_edge(0, 1, input);
    boost::add_edge(1, 2, input);
    boost::add_edge(2, 0, input);
    boost::add_edge(3, 4, input);
    boost::add_edge(4, 5, input);
    boost::add_edge(5, 6, input);
    boost::add_edge(6, 3, input);
    CHECK_THROWS(PlanarizationProcessor(input));
}

TEST_CASE("decomposition into components") {
    SimpleGraph input;
    boost::add_edge(0, 1, input);
    boost::add_edge(1, 2, input);
    boost::add_edge(2, 0, input);
    boost::add_edge(3, 4, input);
    boost::add_edge(4, 5, input);
    boost::add_edge(5, 6, input);
    boost::add_edge(6, 3, input);
    ComponentProcessor cp(input);
    cp.generate_connected_components();
    REQUIRE(cp.components.size() == 2);
    REQUIRE(boost::edge(0, 1, cp.components[0]).second);
    REQUIRE(boost::edge(1, 2, cp.components[0]).second);
    REQUIRE(boost::edge(2, 0, cp.components[0]).second);
    REQUIRE(boost::num_vertices(cp.components[0]) == 3);
    REQUIRE(boost::edge(0, 1, cp.components[1]).second);
    REQUIRE(boost::edge(1, 2, cp.components[1]).second);
    REQUIRE(boost::edge(2, 3, cp.components[1]).second);
    REQUIRE(boost::edge(3, 0, cp.components[1]).second);
    REQUIRE(boost::num_vertices(cp.components[1]) == 4);
    unsigned long vertex_count = 0;
    for (const auto& component: cp.components) {
        vertex_count += boost::num_vertices(component);
    }
    REQUIRE(vertex_count == 7);
    for (auto &component : cp.components) {
        boost::write_graphviz(std::cout, component);
    }
}