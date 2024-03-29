from graph import OurGraph, RegularGraph, BioGraph
from graph_pair import GraphPair
from testing.bfs import get_bfs
from utils import assert_valid_nid, Timer, get_save_path, \
    create_dir_if_not_exists, save
import networkx as nx
from collections import defaultdict, OrderedDict
import numpy as np
import random
from os.path import join, exists
from warnings import warn
import sys
'''
######### for PGNN #########
import torch
import config
from pgnn.utils import precompute_dist_data, preselect_anchor, get_num_anchors
############################
'''


class OurDataset(object):
    def __init__(self, name, gs1, gs2,graphs, natts, eatts, pairs, tvt, align_metric,
                 node_ordering, glabel, loaded_dict, mini=None, my=None):
        if loaded_dict is not None:  # restore from content loaded from disk
            self.__dict__ = loaded_dict
            self._check_invariants()
            return
        self.my=my
        self.name = name

        self.gs = graphs
        self.gs_map = self._gen_gs_map()  # a dict that maps gid to id, id used for enumerating the dataset
        self.id_map = self._gen_id_map() # a dict that maps id to gid #TODO see if we can remove this
        self.natts = natts
        self.eatts = eatts
        self.pairs = pairs  # a dict that maps (gid1, gid2) to GraphPair
        self.tvt = tvt
        self.align_metric = align_metric
        if mini==None:
            if node_ordering == 'bfs':
                self._apply_bfs()
            self.node_ordering = node_ordering
        else:
            self.node_ordering = ""
        self.glabel = glabel
        assert glabel in ['random', 'discrete', 'continuous', None]
        self._check_invariants()
        self.mini=mini
        if mini==None:
            self.stats = self._gen_stats()
        self.gs1_gids = [g.gid() for g in gs1]
        self.gs2_gids = [g.gid() for g in gs2]

    def gs1(self):
        return self._gen_gs_from_gid_list(self.gs1_gids)

    def gs2(self):
        return self._gen_gs_from_gid_list(self.gs2_gids)

    def _gen_gs_from_gid_list(self, gid_list):
        return [self.look_up_graph_by_gid(gid) for gid in gid_list]

    def check(self):
        return (self.gs[2].get_nxgraph())

    def _check_invariants(self):
        self._assert_nonempty_str(self.name)
        assert self.gs and type(self.gs) is list, type(self.gs)
        assert self.gs_map and type(self.gs_map) is dict
        # print("self.gs",self.gs)
        # print("self.gs_map",self.gs_map)
        assert len(self.gs) == len(self.gs_map)
        assert type(self.natts) is list
        for natt in self.natts:
            self._assert_nonempty_str(natt)
        assert type(self.eatts) is list
        for eatt in self.eatts:
            self._assert_nonempty_str(eatt)
        self._check_pairs()
        self._assert_nonempty_str(self.tvt)
        self._assert_nonempty_str(self.align_metric)
        self._check_types()
        # self._check_glabel()

    def _check_pairs(self):
        assert type(self.pairs) is dict  # may have zero pairs
        for (gid1, gid2), pair in self.pairs.items():
            assert gid1 in self.gs_map and gid2 in self.gs_map, \
                '{} {}'.format(gid1, gid2)
            assert type(pair) is GraphPair

    def _check_types(self):
        for g in self.gs:
            assert isinstance(g, OurGraph)
            # if self.align_metric == '' TODO: finish

    def _check_glabel(self):
        for g in self.gs:
            if self.glabel is None:
                assert 'glabel' not in g.get_nxgraph().graph
            elif self.glabel in ['discrete', 'continuous', 'random']:
                glabel = g.get_nxgraph().graph.get('glabel')
                assert glabel is not None, 'No label in graphs! Load the labels!'
                if self.glabel == 'discrete':
                    assert type(glabel) is int and glabel >= 0
                elif self.glabel == 'contiuous':
                    assert type(glabel) is float
                else:
                    pass  # do not care about random graph labels

    def _assert_nonempty_str(self, s):
        assert s is None or (s and type(s) is str)

    def _apply_bfs(self):  # TODO: CHECK IF THIS IS OK
        non2bfs = {}
        for i, graph in enumerate(self.gs):
            if graph.type() == 'bio_graph' and not graph.is_connected:
                continue
            # get g from gs
            g = graph.get_nxgraph()
            gid = g.graph['gid']

            # get bfs for g
            mapping, _ = get_bfs(g)
            len_check_pre = len(g.nodes)

            # reset node features according to bfs
            idx = [mapping[key] for key in sorted(mapping.keys())]
            init_x_bfs = None  # TODO: why is this here?
            # print(idx)
            if hasattr(g, 'init_x'):
                init_x_bfs = g.init_x[idx]

            # relabel nodes according to bfs ordering
            g = nx.relabel_nodes(g, mapping)
            if init_x_bfs is not None:
                g.init_x = init_x_bfs

            # reset g to bfs ordered g
            self.gs[i] = RegularGraph(g) if graph.type() != 'bio_graph' else BioGraph(g, graph.is_connected)
            non2bfs[gid] = mapping
            len_check_post = len(g.nodes)
            assert (len_check_pre == len_check_post)

        for pair in self.pairs.keys():
            # get pair from pairs
            (gid1, gid2) = pair

            # get the mapping from pair
            old_mapping_list = self.pairs[pair].y_true_dict_list
            if old_mapping_list is None:
                continue
            new_mapping_list = []
            for old_mapping in old_mapping_list:
                # reassign mapping according to bfs ordering
                new_mapping = {}
                for node in old_mapping:
                    mapper1 = non2bfs[gid1]
                    mapper2 = non2bfs[gid2]
                    found_node = old_mapping[node]
                    new_mapping[mapper1[node]] = \
                        mapper2[found_node] if found_node != -1 else -1
                new_mapping_list.append(new_mapping)

            # set the mapping to bfs ordered mapping
            self.pairs[pair].y_true_dict_list = new_mapping_list

    def print_stats(self):
        print('{} Summary of {}'.format('-' * 10, self.name))
        self._print_stats_helper(self.stats, 1)
        print('{} End of summary of {}'.format('-' * 10, self.name))

    def _gen_stats(self):
        stats = OrderedDict()
        stats['#graphs'] = len(self.gs)
        if self.tvt is not None:
            stats['tvt'] = self.tvt
        nn = []
        dens = []
        # natts_stats:
        # node attrib name --> { node attrib value : (count, freq) }
        natts_stats, eatts_stats = OrderedDict(), OrderedDict()
        stats['natts_stats'], stats['eatts_stats'] = natts_stats, eatts_stats
        disconnected = set()
        self._iter_gen_stats(nn, dens, natts_stats, eatts_stats, disconnected)
        # Transform node attrib value count to frequency.
        self._gen_attrib_freq(natts_stats)
        self._gen_attrib_freq(eatts_stats)
        if len(natts_stats) != len(self.natts):
            raise ValueError('Found {} node attributes != specified {}'.format(
                len(natts_stats), len(self.natts)))
        if len(eatts_stats) != len(self.eatts):
            raise ValueError('Found {} edge attributes != specified {}'.format(
                len(natts_stats), len(self.eatts)))
        stats['#disconnected graphs'] = len(disconnected)
        sn = OrderedDict()
        stats['#Nodes'] = sn
        sn['Avg'] = np.mean(nn)
        sn['Std'] = np.std(nn)
        sn['Min'] = np.min(nn)
        sn['Max'] = np.max(nn)
        stats['Avg density'] = np.mean(dens)
        stats['#pairwise results'] = len(self.pairs)
        stats['sqrt(#pairwise results)'] = np.sqrt(len(self.pairs))
        if self.align_metric is not None:
            stats['align_metric'] = self.align_metric
        return stats

    def  _iter_gen_stats(self, nn, dens, natts_stats, eatts_stats, disconnected):
        gids = set()
        for g in self.gs:
            gid = g.gid()
            if gid in gids:
                raise ValueError('Graph IDs must be unique. '
                                 'Found two {}s'.format(gid))
            gids.add(gid)
            g = g.get_nxgraph()  # may contain image data; just get nxgraph
            nn.append(g.number_of_nodes())
            dens.append(nx.density(g))
            for i, (n, ndata) in enumerate(sorted(g.nodes(data=True))):
                # print("n,g",n,len(g.nodes()))
                assert_valid_nid(n, g)
                assert i == n  # 0-based consecutive node ids
                for k, v in ndata.items():
                    self._add_attrib(natts_stats, k, v)
            for i, (n1, n2, edata) in enumerate(sorted(g.edges(data=True))):
                assert_valid_nid(n1, g)
                assert_valid_nid(n2, g)
                for k, v in edata.items():
                    self._add_attrib(eatts_stats, k, v)
            if not nx.is_connected(g):
                disconnected.add(g)
        assert len(gids) == len(self.gs)

    def _add_attrib(self, d, attr_name, attr_value):
        if attr_name not in d:
            d[attr_name] = defaultdict(int)
        d[attr_name][attr_value] += 1

    def _gen_attrib_freq(self, d):
        for k, dic in d.items():
            new_dic = {}
            sum = np.sum(list(dic.values()))
            for v, count in dic.items():
                new_dic[v] = count / sum
            sorted_li = sorted(new_dic.items(), key=lambda x: x[1],
                               reverse=True)  # sort by decreasing freq
            sorted_li = [(x, '{:.2%}'.format(y)) for (x, y) in sorted_li]
            d[k] = sorted_li

    def _print_stats_helper(self, d, indent=0):
        for key, value in d.items():
            print('\t' * indent + str(key), end='')
            if type(value) is dict \
                    or type(value) is defaultdict \
                    or type(value) is OrderedDict:
                print()
                self._print_stats_helper(value, indent + 1)
            else:
                pre = '\t' * (indent + 1)
                if type(value) is list:
                    post = ' ({})'.format(len(value))
                    if len(value) > 6:
                        print(pre + str(value[0:3]) +
                              ' ... ' + str(value[-1:]) + post)
                    else:
                        print(pre + str(value) + post)
                else:
                    print(pre + str(value))

    def _gen_gs_map(self):
        rtn = {}
        # print("in gs map")
        #print(type(self.gs[0]))
        for i, g in enumerate(self.gs):

            rtn[g.gid()] = i
            # print("?",g.gid())

        return rtn

    def _gen_id_map(self):
        assert (hasattr(self, "gs_map"))
        return {id: gid for gid, id in self.gs_map.items()}

    def num_graphs(self):
        return len(self.gs)

    def get_all_pairs(self):
        return self.pairs

    def look_up_graph_by_gid(self, gid):
        self._check_gid_type(gid)
        id = self.gs_map.get(gid)
        if id is None:
            raise ValueError('Cannot find {} out of {} graphs'.format(
                gid, len(self.gs_map)))
        assert 0 <= id < len(self.gs)
        return self.gs[id]
        # else:
        # 	if id==11:
        # 		return self.gs[0]
        # 	elif id==12:
        # 		return self.gs[1]
        # 	elif id==21:
        # 		return self.gs[2]
        # 	elif id==22:
        # 		return self.gs[3]

    def look_up_pair_by_gids(self, gid1, gid2):
        self._check_gid_type(gid1)
        self._check_gid_type(gid2)
        pair = self.pairs.get((gid1, gid2))
        if pair is None:
            pair = self.pairs.get((gid2, gid1))  # TODO: assume symmetric
            if not pair:
                # print(gid1,gid2,(self.pairs))
                # return None
                raise ValueError('Cannot find ({},{}) out of {} pairs'.format(
                    gid1, gid2, len(self.pairs)))
        return pair

    def _check_gid_type(self, gid):
        assert type(gid) is int or type(gid) is np.int64, type(gid)

    def tvt_split(self, split_points, tvt_list):
        if self.tvt != 'all':
            raise ValueError('Dataset {} is already {} '
                             '(cannot be further split)'.
                             format(self.name, self.tvt))
        if not split_points:
            raise ValueError('split_points must be a list of floats '
                             'indicating percentages {}'.format(split_points))
        if len(split_points) + 1 != len(tvt_list):
            raise ValueError('Wrong tvt_list {}'.format(tvt_list))
        t = Timer()
        gid_chunks = self._chunk_gids(split_points)
        print('Done gid_chunks', t.time_msec_and_clear())
        sub_datasets = []
        for i, gids in enumerate(gid_chunks):
            graphs, pairs = \
                self._select_with_gids(gids)
            print('Done _select_with_gids', t.time_msec_and_clear())
            graphs = sorted(graphs, key=lambda x: x.nxgraph.graph["gid"])
            sub_datasets.append(OurDataset(
                self.name, graphs, self.natts, self.eatts, pairs, tvt_list[i],
                self.align_metric, self.node_ordering, self.glabel, None))
            print('Done sub_datasets.append', t.time_msec_and_clear())
        return sub_datasets

    def _chunk_gids(self, split_points):
        gid_chunks = []
        gids = sorted(self.gs_map.keys())
        random.Random(123).shuffle(gids)
        left = 0
        split_indices = [int(len(self.gs) * sp) for sp in split_points]
        for si in split_indices:
            right = left + si
            if type(right) is not int or right <= 0 or right >= len(self.gs):
                raise ValueError('Wrong split_points {}'.format(split_points))
            take = gids[left:right]
            gid_chunks.append(take)
            left = right
        # The last chunk is inferred.
        gid_chunks.append(gids[left:])
        return gid_chunks

    def _select_with_gids(self, want_gids):
        t = Timer()
        graphs = [g for g in self.gs if g.gid() in want_gids]
        print('Done graphs', t.time_msec_and_clear())
        pairs = {}
        for (gid1, gid2), pair in self.pairs.items():
            # Both g1 and g2 need to be in the (one) train/test/... set.
            if gid1 in want_gids and gid2 in want_gids:
                pairs[(gid1, gid2)] = pair
        print('Done pairs', t.time_msec_and_clear())
        return graphs, pairs

    def save_graphs_as_gexf(self):
        fp = join(get_save_path(), 'dataset', '{}_{}_{}'.format(
            self.name, self.tvt, self.node_ordering))
        if exists(fp):
            warn('Already exists; Manually delete: rm -rf {}'.format(fp))
            exit(-1)
        else:
            create_dir_if_not_exists(fp)
        for g in self.gs:
            nx.write_gexf(g.get_nxgraph(), join(fp, '{}.gexf'.format(g.gid())))
        save({'pair_gids': list(self.pairs.keys())}, join(fp, 'pair_gids'), print_msg=True)
        print('Saved {} graphs to {}'.format(len(self.gs), fp))
        print('Use it as:')
        print('gexf_{}'.format(fp))


class OurOldDataset(OurDataset):
    def __init__(self, name, gs1, gs2, all_gs, natts, eatts, pairs, tvt,
                 align_metric, node_ordering, glabel, loaded_dict):
        """
        Our old datasets has two lists of graphs, gs1 and gs2, and the pairwise
        results are stored between gs1 and gs2 as a matrix
        where gs1 is along the row and gs2 is along the column.
        """
        if loaded_dict is not None:  # restore from content loaded from disk
            self.__dict__ = loaded_dict
            return
        super(OurOldDataset, self).__init__(name, all_gs, natts, eatts, pairs,
                                            tvt, align_metric, node_ordering,
                                            glabel, loaded_dict)
        self.stats['gs1'] = len(gs1)
        self.stats['gs2'] = len(gs2)
        self.gs1_gids = [g.gid() for g in gs1]
        self.gs2_gids = [g.gid() for g in gs2]

    def gs1(self):
        return self._gen_gs_from_gid_list(self.gs1_gids)

    def gs2(self):
        return self._gen_gs_from_gid_list(self.gs2_gids)

    def _gen_gs_from_gid_list(self, gid_list):
        return [self.look_up_graph_by_gid(gid) for gid in gid_list]

