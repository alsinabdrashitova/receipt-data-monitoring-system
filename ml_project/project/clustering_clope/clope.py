import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class Cluster:

    def __init__(self, history_count):
        self.history_count_transact = [0] * history_count
        self.area = 0.0
        self.height = 0.0
        self.width = 0.0
        self.gradient = 0.0
        self.count_transactions = 0
        self.histogram = {}

    def add_transaction(self, transaction):
        for item in transaction:
            if not (item in self.histogram):
                self.histogram[item] = 1
            else:
                self.histogram[item] += 1
        self.area += float(len(transaction))
        self.width = float(len(self.histogram))
        self.count_transactions += 1

    def remove_transaction(self, transaction):
        for item in transaction:
            if self.histogram[item] == 0:
                del self.histogram[item]
        self.area -= float(len(transaction))
        self.width = float(len(self.histogram))
        self.count_transactions -= 1
        return self.gradient


class CLOPE:

    def __init__(self, is_save_history=True, print_step=1000, random_seed=None):
        if random_seed is not None:
            self.random_seed = random_seed
        else:
            self.random_seed = np.random.random_integers(0, 65536)
        self.clusters = {}
        self.noise_clusters = {}
        self.count_transactions = 0
        self.iteration = 0
        self.transaction = {}
        self.max_cluster_number = 0
        self.print_step = print_step
        self.is_save_history = is_save_history

    def delta_transaction(self, transaction, cluster_number, r):
        area = self.clusters[cluster_number].area + len(transaction)
        width = self.clusters[cluster_number].width
        for item in transaction:
            if not (item in self.clusters[cluster_number].histogram):
                width += 1
        if width != 0:
            new_delta_value = area * (self.clusters[cluster_number].count_transactions + 1) / (width ** r)
        else:
            new_delta_value = 0
        if self.clusters[cluster_number].width != 0:
            old_delta_value = self.clusters[cluster_number].area * self.clusters[cluster_number].count_transactions / (
                    self.clusters[cluster_number].width ** r)
        else:
            old_delta_value = 0
        return new_delta_value - old_delta_value

    def noise_reduction(self, limit):
        new_clusters = {}
        for item in self.clusters:
            if self.clusters[item].count_transactions > limit:
                new_clusters[item] = self.clusters[item]
            else:
                self.noise_clusters[item] = True
        self.clusters = new_clusters

    def __len__(self):
        return len(self.clusters)

    def get_goal_function(self, r):
        measure = 0.0
        for item in self.clusters:
            if item.width == 0:
                pass
            else:
                measure += item.area / (item.width ** r) * item.count_transactions / self.count_transactions
        return measure

    def move_transaction(self, transaction, id, repulsion=2, max_count_clusters=None):
        r = repulsion
        max_value = None
        max_value_index = None
        self.count_transactions += 1

        for cluster_number in self.clusters:
            if self.is_save_history:
                self.clusters[cluster_number].history_count_transact.append(
                    self.clusters[cluster_number].count_transactions
                )

            delta = self.delta_transaction(transaction, cluster_number, r)
            if (delta > 0 or max_count_clusters is not None) and (max_value is None or delta > max_value):
                max_value_index = cluster_number
                max_value = delta

        if max_count_clusters is None or len(self.clusters) < max_count_clusters:
            self.clusters[self.max_cluster_number] = Cluster(self.count_transactions)
            if max_value is None or self.delta_transaction(transaction, self.max_cluster_number, r) > max_value:
                max_value_index = self.max_cluster_number
                self.max_cluster_number += 1
            else:
                del self.clusters[self.max_cluster_number]

        self.transaction[id] = max_value_index
        self.clusters[max_value_index].add_transaction(transaction)

        return max_value_index

    def get_noise_limit(self, percentile=0.75):
        size_clusters = []
        for item in self.clusters:
            size_clusters.append(self.clusters[item].count_transactions)
        sorted(size_clusters)
        median_element = int(len(size_clusters) * percentile) + 1
        if len(size_clusters) < 5:
            limit = 10
        else:
            limit = size_clusters[median_element]
        return limit

    def init_clusters(self, data, repulsion=2, is_noise_reduction=-1, noise_median_threshold=0.75,
                      max_count_clusters=None):
        index = 0
        keys = sorted(data.keys())
        np.random.seed(self.random_seed)
        np.random.shuffle(keys)
        for item in keys:
            self.move_transaction(data[item], item, repulsion, max_count_clusters)
            index += 1
            if self.print_step > 0 and index % self.print_step == 0:
                print("Итерация: ", self.iteration, ". Номер шага", index, ". Число кластеров: ", len(self.clusters))

        if is_noise_reduction < 0:
            is_noise_reduction = self.get_noise_limit(noise_median_threshold)
        if is_noise_reduction > 0:
            self.noise_reduction(is_noise_reduction)

        self.iteration = 1

    def next_step(self, data, repulsion=2, is_noise_reduction=-1, noise_median_threshold=0.75, max_count_clusters=None):
        if is_noise_reduction < 0:
            is_noise_reduction = self.get_noise_limit(noise_median_threshold)
        self.noise_reduction(is_noise_reduction)

        index = 0
        eps = 0
        keys = sorted(data.keys())
        np.random.seed(self.random_seed)
        np.random.shuffle(keys)
        for id in keys:
            cluster_number = self.transaction[id]
            transaction = data[id]
            if cluster_number in self.noise_clusters:
                eps += 0
            else:
                self.clusters[cluster_number].remove_transaction(transaction)
                eps += int(
                    self.move_transaction(transaction, id, repulsion, max_count_clusters)
                    !=
                    cluster_number
                )

            index += 1
            if self.print_step is not None and self.print_step > 0 and index % self.print_step == 0:
                print("Итерация: ", self.iteration, ". Номер шага", index, ". Число кластеров: ", len(self.clusters))
        self.iteration += 1

        self.noise_reduction(is_noise_reduction)
        return eps

    def print_history_count(self, repulsion, seed):
        len_history = len(list(self.clusters.values())[0].history_count_transact)
        for index_cluster in self.clusters:
            item_cluster = self.clusters[index_cluster]
            x = np.array(range(0, len_history))
            if len(item_cluster.history_count_transact) != 0:
                y = item_cluster.history_count_transact
            else:
                y = np.array(range(0, len_history))
            plt.plot(x, y)
        plt.xlabel(u"Номер итерации")
        plt.ylabel(u"Количество транзакций")
        plt.title(u"Количество транзакций в различных кластерах. \nКоличество кластеров: " + str(len(self.clusters)) +
                  u".\n Отталкивание: " + str(repulsion) + ". Seed: " + str(seed))
        plt.show()
