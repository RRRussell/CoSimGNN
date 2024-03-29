"""
OurLossFunction designed for matrix based matching,
i.e. Subsgraph Isomorphism Network + Multi-Level Graph Matching,
"""
from batch import create_edge_index
from config import FLAGS
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GINConv


class OurLossFunction(nn.Module):
    def __init__(self, n_features, alpha, beta, gamma, tau, y_from, z_from,
                 theta=FLAGS.theta):
        super(OurLossFunction, self).__init__()
        self.fc1 = nn.Linear(n_features, n_features)
        self.fc2 = nn.Linear(n_features, n_features)
        self.fc3 = nn.Linear(n_features, n_features)
        nn1 = lambda x: x
        nn2 = lambda x: x
        nn3 = lambda x: x
        self.conv1 = GINConv(nn1)
        self.conv2 = GINConv(nn2)
        self.conv3 = GINConv(nn3)
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.theta = theta
        self.tau = tau
        self.y_from = y_from
        self.z_from = z_from

    def forward(self, _, batch_data, *unused):
        # conversion code
        pair_list = batch_data.pair_list
        # initialize loss
        loss = 0.0
        num_samples = len(pair_list)
        for i, pair in enumerate(pair_list):
            ####################################
            # post-processing: convert X -> Y,Z
            ####################################
            # unpack pair
            g1, g2 = pair.g1.get_nxgraph(), pair.g2.get_nxgraph()
            N, M = g1.number_of_nodes(), g2.number_of_nodes()

            y_preds = self._get_y(pair) # list of matrices
            z_preds_g1, z_preds_g2 = self._get_z(pair) # two lists of vectors

            matching_matrix_comp_flag = z_preds_g1 is not None and z_preds_g2 is not None
            if not matching_matrix_comp_flag:
                assert self.beta == 0 and self.gamma == 0 and self.tau == 0

            # obtain 1st ground truth
            y_true_dict_list = pair.get_y_true_list_dict_view()
            print("---------------------------")
            print("y_true_dict_list",y_true_dict_list)
            assert len(y_true_dict_list) >= 1
            y_true_dict = y_true_dict_list[0]

            # construct ground truth matrix
            y_true = torch.zeros((N, M), device=FLAGS.device)
            if matching_matrix_comp_flag:
                z_true_g1 = torch.zeros_like(z_preds_g1[0])
                z_true_g2 = torch.zeros_like(z_preds_g2[0])
            for nid1 in y_true_dict.keys():
                nid2 = y_true_dict[nid1]
                y_true[nid1, nid2] = 1
                if matching_matrix_comp_flag:
                    z_true_g1[nid1] = 1
                    z_true_g2[nid2] = 1

            ####################################
            # loss function: convert Y,Z -> loss
            ####################################

            # iterate through all the heads
            cvt_init_x = lambda x: torch.tensor(x, dtype=torch.float).to(FLAGS.device)
            # cvt_edges = lambda x: torch.t(torch.tensor(list(x), dtype=torch.long)).to(FLAGS.device)
            cand_losses = []
            for j in range(len(y_preds)):
                y_pred = y_preds[j]
                if matching_matrix_comp_flag:
                    z_pred_g1, z_pred_g2 = z_preds_g1[j], z_preds_g2[j]

                ###########
                # LOSS 1: Matching-level MCS loss (main)
                ###########
                loss_1 = torch.sum(-1 * y_true * torch.log(y_pred + 1e-12)) \
                         / (torch.sum(y_true) + 1e-12)

                if matching_matrix_comp_flag:
                    ###########
                    # LOSS 2: Node-level MCS loss
                    ###########
                    loss_2 = \
                    (
                        (
                            torch.sum(-1 * z_true_g1 * torch.log(z_pred_g1 + 1e-12)) +
                            torch.sum(-1 * (1 - z_true_g1) * torch.log(1 - z_pred_g1 + 1e-12))
                        ) / len(z_true_g1) +
                        (
                            torch.sum(-1 * z_true_g2 * torch.log(z_pred_g2 + 1e-12)) + \
                            torch.sum(-1 * (1 - z_true_g2) * torch.log(1 - z_pred_g2 + 1e-12)) \
                        ) / len(z_true_g2)
                    ) / 2

                    ###########
                    # LOSS 3: Graph-level MCS loss
                    ###########

                    # Normalized MSE
                    loss_3 = ((torch.sum(y_pred) - torch.sum(y_true)) / ((N + M) / 2)) ** 2

                    ###########
                    # LOSS 4: Subgraph Isomorphism Loss
                    ###########
                    if self.training:
                        # get initial features
                        x1, x2 = cvt_init_x(g1.init_x), cvt_init_x(g2.init_x)
                        # get edge_list
                        edge_list1, edge_list2 = create_edge_index(g1), create_edge_index(g2)
                        # get subgraph embeddings
                        u1 = self._get_subgraph_embedding(x1, z_pred_g1, edge_list1)
                        u2 = self._get_subgraph_embedding(x2, z_pred_g2, edge_list2)
                        # Normalized Frobenius Norm for Loss
                        loss_4 = (torch.sum(u1 - u2) / u1.shape[0]) ** 2
                    else:
                        loss_4 = 0.0

                    # Compute candidate loss for given output
                    cand_loss = self.alpha * loss_1 + self.beta * loss_2 \
                                + self.gamma * loss_3 + self.tau * loss_4
                else:
                    cand_loss = self.alpha * loss_1

                cand_losses.append(cand_loss)
            # Only use the minimum of candidate losses
            loss += min(cand_losses)

        # Normalize by batch_size
        loss /= num_samples

        return loss

    def _get_y(self, pair):
        if self.y_from == 'y_pred':
            return pair.get_y_pred_list_mat_view(
                format='torch_{}'.format(FLAGS.device))
        elif self.y_from == 'tree_pred_hard':
            return [state.tree_pred for state in pair.state_list]
        elif self.y_from == 'tree_pred_soft':
            return [state.tree_pred_soft for state in pair.state_list]
        else:
            assert False

    def _get_z(self, pair):
        if self.z_from == 'z_pred':
            return pair.z_pred
        elif self.z_from == 'hidden_state_v_hard':
            return [state.v1 for state in pair.state_list], \
                   [state.v2 for state in pair.state_list]
        elif self.z_from == 'hidden_state_v_soft':
            return [state.v1_soft for state in pair.state_list], \
                   [state.v2_soft for state in pair.state_list]
        else:
            assert False

    def _get_subgraph_embedding(self, x, z_pred, edge_list):
        thresh = self.theta
        mask = (z_pred > thresh).type(torch.FloatTensor).to(FLAGS.device)
        x = torch.t(mask * torch.t(x))
        x = F.relu(self.conv1(x, edge_list))
        x = torch.t(mask * torch.t(x))  # torch.t(z_pred * torch.t(x))
        x = F.relu(self.conv2(x, edge_list))
        x = torch.t(mask * torch.t(x))  # torch.t(z_pred * torch.t(x))
        x = F.relu(self.conv3(x, edge_list))
        x = torch.t(mask * torch.t(x))
        x = torch.sum(x, dim=0)
        return x
