from solve_parent_dir import solve_parent_dir
from dataset_config import get_dataset_conf
from dist_sim import get_ds_metric_config
from utils import format_str_list, C, get_user, get_host
import argparse
import torch

solve_parent_dir()
parser = argparse.ArgumentParser()

"""
Data.
"""
dataset = 'BA60'
parser.add_argument('--dataset', default=dataset)

dataset_version = None  # 'v2'
parser.add_argument('--dataset_version', default=dataset_version)

filter_large_size = None 
parser.add_argument('--filter_large_size', type=int, default=filter_large_size)  # None or >= 1

select_node_pair = None
parser.add_argument('--select_node_pair', type=str, default=select_node_pair)  # None or gid1_gid2

c = C()#counting
parser.add_argument('--node_fe_{}'.format(c.c()), default='one_hot')

# parser.add_argument('--node_fe_{}'.format(c.c()),
#                     default='local_degree_profile')

natts, eatts, tvt_options, align_metric_options, *_ = \
    get_dataset_conf(dataset)

""" Must use exactly one alignment metric across the entire run. """
#align_metric = align_metric_options[0]
#if len(align_metric_options) == 2:
""" Choose which metric to use. """
#align_metric = 'ged'
align_metric = 'mcs'
parser.add_argument('--align_metric', default=align_metric)

#dos_true="dist"
dos_true = "sim"
parser.add_argument('--dos_true', default=dos_true)

# Assume the model predicts None. May be updated below.
dos_pred = "sim"

parser.add_argument('--node_feats', default=format_str_list(natts))

parser.add_argument('--edge_feats', default=format_str_list(eatts))
"""
Evaluation.
"""

parser.add_argument('--tvt_options', default=format_str_list(tvt_options))

""" holdout, (TODO) <k>-fold. """
tvt_strategy = 'holdout'
parser.add_argument('--tvt_strategy', default=tvt_strategy)

if tvt_strategy == 'holdout':
    if tvt_options == ['all']:
        parser.add_argument('--train_test_ratio', type=float, default=0.8)
    elif tvt_options == ['train', 'test']:
        pass
    else:
        raise NotImplementedError()
else:
    raise NotImplementedError()

parser.add_argument('--debug', type=bool, default='debug' in dataset)

# Assume normalization is needed for true dist/sim scores.
parser.add_argument('--ds_norm', type=bool, default=True)
#parser.add_argument('--ds_norm', type=bool, default=False)

parser.add_argument('--ds_kernel', default='exp')

"""
Model.
"""
parser.add_argument('--model')

dataset = "BA"
parser.add_argument('--our_dataset', type=str, default=dataset)

traditional_method = False
#traditional_method = True
parser.add_argument('--traditional_method', type=bool, default=traditional_method)

num_select = 3
parser.add_argument('--num_select', default=num_select)

n_outputs = 10 # TODO: tune this
parser.add_argument('--n_outputs', type=int, default=n_outputs)

hard_mask = True
parser.add_argument('--hard_mask', type=bool, default=hard_mask)

model_name = 'fancy'
parser.add_argument('--model_name', default=model_name)

c = C()

D = 64

parser.add_argument('--theta', type=float, default=0.5)

# Finally we set dos_pred.
parser.add_argument('--dos_pred', default=dos_pred)

"""
Optimization.
"""
lr = 1e-3
parser.add_argument('--lr', type=float, default=lr)

gpu = 0
device = str('cuda:{}'.format(gpu) if torch.cuda.is_available() and gpu != -1
             else 'cpu')
parser.add_argument('--device', default=device)

sub_graph_path = "../../sub_graph/"
parser.add_argument('--sub_graph_path', type=str, default=sub_graph_path)

num_epochs = None
parser.add_argument('--num_epochs', default=num_epochs)

num_iters = 2000
parser.add_argument('--num_iters', type=int, default=num_iters)

validation = False  # TODO: tune this
parser.add_argument('--validation', type=bool, default=validation)

throw_away = 0  # TODO: tune this
parser.add_argument('--throw_away', type=float, default=throw_away)

print_every_iters = 10
parser.add_argument('--print_every_iters', type=int, default=print_every_iters)

only_iters_for_debug = None  # only train and test this number of pairs
parser.add_argument('--only_iters_for_debug', type=int, default=only_iters_for_debug)

save_model = True  # TODO: tune this
parser.add_argument('--save_model', type=bool, default=save_model)

load_model =  None

parser.add_argument('--load_model', default=load_model)

batch_size = 128
parser.add_argument('--batch_size', type=int, default=batch_size)

num_node_feat = 30
parser.add_argument('--num_node_feat', type=bool, default=num_node_feat)
# draw_sub_graph = True
draw_sub_graph = False
parser.add_argument('--draw_sub_graph', type=bool, default=draw_sub_graph)

# save_sub_graph = True
save_sub_graph = False
parser.add_argument('--save_sub_graph', type=bool, default=save_sub_graph)

save_every_epochs = 1
parser.add_argument('--save_every_epochs', type=int, default=save_every_epochs)

parser.add_argument('--node_ordering', default='bfs')
parser.add_argument('--no_probability', default=False)
parser.add_argument('--positional_encoding', default=False)  # TODO: dataset.py cannot see this

"""
Other info.
"""
parser.add_argument('--user', default=get_user())

parser.add_argument('--hostname', default=get_host())

temp = parser.parse_args()
model = temp.model

########################################
# Node Embedding
########################################
if model == 'GCN-Mean':
    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,output_dim={},act=relu,bn=True'.format(D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'AVG_Pooling:input_dim={},end_pooling=False,max_pooling=False,global_pool=False'.format(D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'AVG_Pooling:input_dim={},end_pooling=True,max_pooling=False,global_pool=False'.format(D)
    parser.add_argument(n, default=s)

elif model == 'GCN-Max':
    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,output_dim={},act=relu,bn=True'.format(D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'AVG_Pooling:input_dim={},end_pooling=False,max_pooling=True'.format(D)
    parser.add_argument(n, default=s)
    n = '--layer_{}'.format(c.c())
    s = 'AVG_Pooling:input_dim={},end_pooling=False,max_pooling=True'.format(D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    parser.add_argument(n, default=s)
    n = '--layer_{}'.format(c.c())
    s = 'AVG_Pooling:input_dim={},end_pooling=False,max_pooling=True'.format(D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'AVG_Pooling:input_dim={},end_pooling=True,max_pooling=True'.format(D)
    parser.add_argument(n, default=s)

elif model == 'simgnn':
    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,output_dim={},act=relu,bn=False'.format(D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,input_dim={},output_dim={},act=relu,bn=False'.format(D, D // 2)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,input_dim={},output_dim={},act=relu,bn=False'.format(D // 2, D // 2 // 2)

    # D //= 2
    parser.add_argument(n, default=s)
    
    n = '--layer_{}'.format(c.c())
    input_dim = 16
    att_times = 1
    att_num = 1
    att_style = 'dot'
    att_weight = True
    feature_map_dim = 16
    bias = True
    ntn_inneract = "relu" #tanh, relu before
    apply_u = False#True
    mne_inneract = "relu" #sigmoid
    mne_method = 'hist_16'
    branch_style = 'an'
    reduce_factor = 2
    criterion = 'MSELoss'
    s = 'simgnn:input_dim={},att_times={},att_num={},att_style={},att_weight={},feature_map_dim={},bias={},ntn_inneract={},apply_u={},mne_inneract={},mne_method={},branch_style={},reduce_factor={},criterion={}'.\
    format(input_dim, att_times, att_num, att_style,att_weight, feature_map_dim, bias, ntn_inneract, apply_u, mne_inneract, mne_method, branch_style, reduce_factor, criterion)
    parser.add_argument(n, default=s)

elif model == 'gsim_cnn':
    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,output_dim={},act=relu,bn=True'.format(D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D // 2)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gcn,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D // 2, D // 2 // 2)
    # D //= 2
    parser.add_argument(n, default=s)
    
    n = '--layer_{}'.format(c.c())
    gcn_num = 3
    fix_size = 10
    mode = 0
    padding_value = 0
    align_corners =  False
    s = 'GraphConvolutionCollector:gcn_num={},fix_size={},mode={},padding_value={},align_corners={}'. \
        format(gcn_num, fix_size, mode, padding_value, align_corners)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    in_channels = 1
    out_channels = 16
    kernel_size = 6
    stride = 1
    gcn_num = 3
    bias = True
    poolsize = 2
    act = 'relu'
    end_cnn = False
    s = 'CNN:in_channels={},out_channels={},kernel_size={},stride={},gcn_num={},bias={},poolsize={},act={},end_cnn={}'. \
        format(in_channels, out_channels, kernel_size, stride, gcn_num, bias, poolsize, act, end_cnn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    in_channels = 16
    out_channels = 32
    kernel_size = 6
    stride = 1
    gcn_num = 3
    bias = True
    poolsize = 2
    act = 'relu'
    end_cnn = False
    s = 'CNN:in_channels={},out_channels={},kernel_size={},stride={},gcn_num={},bias={},poolsize={},act={},end_cnn={}'. \
        format(in_channels, out_channels, kernel_size, stride, gcn_num, bias, poolsize, act, end_cnn)
    parser.add_argument(n, default=s)


    n = '--layer_{}'.format(c.c())
    in_channels = 32
    out_channels = 64
    kernel_size = 5
    stride = 1
    gcn_num = 3
    bias = True
    poolsize = 2
    act = 'relu'
    end_cnn = False
    s = 'CNN:in_channels={},out_channels={},kernel_size={},stride={},gcn_num={},bias={},poolsize={},act={},end_cnn={}'. \
        format(in_channels, out_channels, kernel_size, stride, gcn_num, bias, poolsize, act, end_cnn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    in_channels = 64
    out_channels = 128
    kernel_size = 5
    stride = 1
    gcn_num = 3
    bias = True
    poolsize = 3
    act = 'relu'
    end_cnn = False
    s = 'CNN:in_channels={},out_channels={},kernel_size={},stride={},gcn_num={},bias={},poolsize={},act={},end_cnn={}'. \
        format(in_channels, out_channels, kernel_size, stride, gcn_num, bias, poolsize, act, end_cnn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    in_channels = 128
    out_channels = 128
    kernel_size = 5
    stride = 1
    gcn_num = 3
    bias = True
    poolsize = 3
    act = 'relu'
    end_cnn = True
    s = 'CNN:in_channels={},out_channels={},kernel_size={},stride={},gcn_num={},bias={},poolsize={},act={},end_cnn={}'. \
        format(in_channels, out_channels, kernel_size, stride, gcn_num, bias, poolsize, act, end_cnn)
    parser.add_argument(n, default=s)

elif model =='GMN':

    n = '--layer_{}'.format(c.c())
    s = 'GMNEncoder:output_dim={},act=relu'.format(D)
    parser.add_argument(n, default=s)

    more_nn = None  # 'EdgeConv'  # None, 'EdgeConv'

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={},enhance=False'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={},enhance=False'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={},enhance=False'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={},enhance=False'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={},enhance=False'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNAggregator:input_dim={},output_dim={}'.format(D, D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNLoss:ds_metric=cosine'
    parser.add_argument(n, default=s)

elif model == 'CoSim-CNN':

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,output_dim={},act=relu,bn=True'. \
        format(D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'Poolings:heads={},input_dim={},output_num={},output_dim={},CosimGNN={}'.format(5,D,10,D,True)
    parser.add_argument(n, default=s)

    more_nn = None  # 'EdgeConv'  # None, 'EdgeConv'

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    gcn_num = 3
    fix_size = 10
    mode = 0
    padding_value = 0
    align_corners = False
    s = 'GraphConvolutionCollector:gcn_num={},fix_size={},mode={},padding_value={},align_corners={}'. \
        format(gcn_num, fix_size, mode, padding_value, align_corners)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    in_channels = 1
    out_channels = 16
    kernel_size = 6
    stride = 1
    gcn_num = 3
    bias = True
    poolsize = 2
    act = 'relu'
    end_cnn = False
    s = 'CNN:in_channels={},out_channels={},kernel_size={},stride={},gcn_num={},bias={},poolsize={},act={},end_cnn={}'. \
        format(in_channels, out_channels, kernel_size, stride, gcn_num, bias, poolsize, act, end_cnn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    in_channels = 16
    out_channels = 32
    kernel_size = 6
    stride = 1
    gcn_num = 3
    bias = True
    poolsize = 2
    act = 'relu'
    end_cnn = False
    s = 'CNN:in_channels={},out_channels={},kernel_size={},stride={},gcn_num={},bias={},poolsize={},act={},end_cnn={}'. \
        format(in_channels, out_channels, kernel_size, stride, gcn_num, bias, poolsize, act, end_cnn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    in_channels = 32
    out_channels = 64
    kernel_size = 5
    stride = 1
    gcn_num = 3
    bias = True
    poolsize = 2
    act = 'relu'
    end_cnn = False
    s = 'CNN:in_channels={},out_channels={},kernel_size={},stride={},gcn_num={},bias={},poolsize={},act={},end_cnn={}'. \
        format(in_channels, out_channels, kernel_size, stride, gcn_num, bias, poolsize, act, end_cnn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    in_channels = 64
    out_channels = 128
    kernel_size = 5
    stride = 1
    gcn_num = 3
    bias = True
    poolsize = 3
    act = 'relu'
    end_cnn = False
    s = 'CNN:in_channels={},out_channels={},kernel_size={},stride={},gcn_num={},bias={},poolsize={},act={},end_cnn={}'. \
        format(in_channels, out_channels, kernel_size, stride, gcn_num, bias, poolsize, act, end_cnn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    in_channels = 128
    out_channels = 128
    kernel_size = 5
    stride = 1
    gcn_num = 3
    bias = True
    poolsize = 3
    act = 'relu'
    end_cnn = True
    s = 'CNN:in_channels={},out_channels={},kernel_size={},stride={},gcn_num={},bias={},poolsize={},act={},end_cnn={}'. \
        format(in_channels, out_channels, kernel_size, stride, gcn_num, bias, poolsize, act, end_cnn)
    parser.add_argument(n, default=s)

elif model == 'CoSim-Mem':
    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,output_dim={},act=relu,bn=True'. \
        format(D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'Poolings:heads={},input_dim={},output_num={},output_dim={},CosimGNN=False'.format(5, D, 10, D)
    parser.add_argument(n, default=s)

    more_nn = None  # 'EdgeConv'  # None, 'EdgeConv'

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={}'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={}'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={}'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNAggregator:input_dim={},output_dim={}'.format(D, D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNLoss:ds_metric=cosine'
    parser.add_argument(n, default=s)

elif model == 'CoSim-ATT':
    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,output_dim={},act=relu,bn=True'. \
        format(D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    input_dim = D
    att_times = 1
    att_num = 1
    att_style = 'dot'
    att_weight = True
    feature_map_dim = 16
    bias = True
    ntn_inneract = "relu"  # tanh, relu before
    apply_u = False  # True
    mne_inneract = "relu"  # sigmoid
    mne_method = 'hist_16'
    branch_style = 'an'
    reduce_factor = 2
    criterion = 'MSELoss'
    s = 'simgnn_pool:input_dim={},att_times={},att_num={},att_style={},att_weight={},feature_map_dim={},bias={},ntn_inneract={},apply_u={},mne_inneract={},mne_method={},branch_style={},reduce_factor={},criterion={}'. \
        format(input_dim, att_times, att_num, att_style, att_weight, feature_map_dim, bias, ntn_inneract, apply_u,
               mne_inneract, mne_method, branch_style, reduce_factor, criterion)
    parser.add_argument(n, default=s)

    more_nn = None  # 'EdgeConv'  # None, 'EdgeConv'

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={}'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={}'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={}'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNAggregator:input_dim={},output_dim={}'.format(D, D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNLoss:ds_metric=cosine'
    parser.add_argument(n, default=s)

elif model == 'CoSim-SAG':
    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,output_dim={},act=relu,bn=True'. \
        format(D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'Diff_Pooling:pool_type=sag,ratio={}'.format(10)
    parser.add_argument(n, default=s)

    more_nn = None  # 'EdgeConv'  # None, 'EdgeConv'

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={}'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={}'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={}'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNAggregator:input_dim={},output_dim={}'.format(D, D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNLoss:ds_metric=cosine'
    parser.add_argument(n, default=s)

elif model == 'CoSim-TOPK':
    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,output_dim={},act=relu,bn=True'. \
        format(D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'Diff_Pooling:pool_type=topk,ratio={}'.format(10)
    parser.add_argument(n, default=s)

    more_nn = None  # 'EdgeConv'  # None, 'EdgeConv'

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={}'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={}'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={}'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNAggregator:input_dim={},output_dim={}'.format(D, D)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNLoss:ds_metric=cosine'
    parser.add_argument(n, default=s)

elif model == 'CoSim-GNN10':

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,output_dim={},act=relu,bn=True'. \
        format(D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'Poolings:heads={},input_dim={},output_num={},output_dim={},CosimGNN=True'.format(5,D,10,D)
    parser.add_argument(n, default=s)

    more_nn = None  # 'EdgeConv'  # None, 'EdgeConv'

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={},enhance=True'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={},enhance=True'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={},enhance=True'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNAggregator:input_dim={},output_dim={}'.format(D, D)
    parser.add_argument(n, default=s)


    n = '--layer_{}'.format(c.c())
    s = 'GMNLoss:ds_metric=cosine'
    parser.add_argument(n, default=s)

elif model == 'CoSim-GNN1':

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,output_dim={},act=relu,bn=True'. \
        format(D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'NodeEmbedding:type=gin,input_dim={},output_dim={},act=relu,bn=True'. \
        format(D, D)
    # D //= 2
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'Poolings:heads={},input_dim={},output_num={},output_dim={},CosimGNN=True'.format(5,D,1,D)
    parser.add_argument(n, default=s)

    more_nn = None  # 'EdgeConv'  # None, 'EdgeConv'

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={},enhance=True'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={},enhance=True'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNPropagator:input_dim={},' \
        'output_dim={},distance_metric=cosine,more_nn={},enhance=True'.format(D, D, more_nn)
    parser.add_argument(n, default=s)

    n = '--layer_{}'.format(c.c())
    s = 'GMNAggregator:input_dim={},output_dim={}'.format(D, D)
    parser.add_argument(n, default=s)


    n = '--layer_{}'.format(c.c())
    s = 'GMNLoss:ds_metric=cosine'
    parser.add_argument(n, default=s)

parser.add_argument('--layer_num', type=int, default=c.t())
FLAGS = parser.parse_args()