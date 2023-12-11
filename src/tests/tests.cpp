#include <catch2/catch_test_macros.hpp>
#include <boost/graph/graphviz.hpp>

#include "../simple_graph.hpp"
#include "../planarization_processor.hpp"
#include "../component_processor.hpp"
#include "../bc_tree_generator.hpp"

TEST_CASE("generate dfs spanning tree") {
    simple_graph_t input(5);
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
    simple_graph_t input;
    boost::add_edge(0, 1, input);
    boost::add_edge(1, 2, input);
    boost::add_edge(2, 0, input);
    boost::add_edge(3, 4, input);
    boost::add_edge(4, 5, input);
    boost::add_edge(5, 6, input);
    boost::add_edge(6, 3, input);
    PlanarizationProcessor pp(input);
    CHECK_THROWS(pp.generate_dfs_spanning_tree());
}

TEST_CASE("decomposition into components") {
    simple_graph_t input;
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

TEST_CASE("bc_tree identify cutvertices and blocks"){
    /*this is the graph from boost documentation*/
    simple_graph_t input(9);
    auto B_C_edge = boost::add_edge(1, 2, input); //B C
    boost::add_edge(1, 3, input); //B D
    auto C_D_edge = boost::add_edge(2, 3, input); //C D

    boost::add_edge(0, 1, input); //A B
    boost::add_edge(0, 5, input); //A F
    auto B_E_edge = boost::add_edge(1, 4, input); //B E
    boost::add_edge(4, 5, input); //E F

    auto A_G_edge = boost::add_edge(0, 6, input); //A G

    boost::add_edge(6, 7, input); //G H
    boost::add_edge(6, 8, input); //G I
    boost::add_edge(7, 8, input); //H I

    BCTreeGenerator bc(input);
    bc.generate_bc_tree();
    REQUIRE(bc.articulation_points.size() == 3);
    REQUIRE(std::find(bc.articulation_points.begin(), bc.articulation_points.end(), 0) != bc.articulation_points.end()); // A
    REQUIRE(std::find(bc.articulation_points.begin(), bc.articulation_points.end(), 1) != bc.articulation_points.end()); // B
    REQUIRE(std::find(bc.articulation_points.begin(), bc.articulation_points.end(), 6) != bc.articulation_points.end()); // G

    auto edge_it = boost::edges(input);
    for(auto it = edge_it.first; it != edge_it.second; it++) {
        std::cout << *it << " " << input[*it].bicomponent_id << std::endl;
    }
}