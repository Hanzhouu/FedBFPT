#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:HanZhou
# datetime:2022/7/25 20:31
# software: PyCharm
import os

import natsort

os.environ["CUDA_VISIBLE_DEVICES"] = '0,1,2,3'
import torch
from transformers import BertConfig, BertForMaskedLM

import utils
from pretraining import dp_pretrain
import shutil


# def rebuild_test():
#     fed_epoch = 3
#     layer_num = 6
#
#     model_path = './model/bert-base-uncased/'
#
#     modelConfig = BertConfig.from_pretrained(model_path)
#     ori_model = BertForMaskedLM.from_pretrained(model_path, config=modelConfig)
#
#     modelConfig.num_hidden_layers = layer_num  # 相当于构建一个小模型，transformer层只有六层
#     model = BertForMaskedLM.from_pretrained(model_path, config=modelConfig)
#
#     for i in range(fed_epoch):
#         print("Epoch:%d" % i)
#         model = utils.rebuild_model(model, layer_num - i - 1, i + 1)
#
#         ori_param = []
#         for layer in ori_model.bert.encoder.layer[:i + 1]:
#             for p in layer.parameters():
#                 ori_param.append(p.data)
#         train_param = []
#         for layer in ori_model.bert.encoder.layer[:i + 1]:
#             for p in layer.parameters():
#                 train_param.append(p.data)
#
#         for x, y in zip(ori_param, train_param):
#             if torch.equal(x, y):
#                 continue
#             else:
#                 print("Fail")
#
#         print("---------------------------------")
#         model = utils.train_trans_layer(model, [i])  # 只训练transformers层的第i层
#         for name, param in model.named_parameters():
#             if param.requires_grad:
#                 print(name)


# def update_test():
#     param_container = utils.create_container()
#
#     param_dict = './outputs/params/Biology/RandomLayer_06/'
#     param_read = param_dict + 'client_' + str(5) + '.pt'
#     param_test = torch.load(param_read)
#     for name in param_test:
#         print(name)
#     print("------------------------------------")
#
#     first_name = 'bert.encoder.layer.'
#     last_name_list = [".attention.self.query.weight",
#                       ".attention.self.query.bias",
#                       ".attention.self.key.weight",
#                       ".attention.self.key.bias",
#                       ".attention.self.value.weight",
#                       ".attention.self.value.bias",
#                       ".attention.output.dense.weight",
#                       ".attention.output.dense.bias",
#                       ".attention.output.LayerNorm.weight",
#                       ".attention.output.LayerNorm.bias",
#                       ".intermediate.dense.weight",
#                       ".intermediate.dense.bias",
#                       ".output.dense.weight",
#                       ".output.dense.bias",
#                       ".output.LayerNorm.weight",
#                       ".output.LayerNorm.bias"]
#     for x in last_name_list:
#         print(first_name + str(0) + x)
#
#         # name_list = name.split('.')
#         # print(name_list[3])


def pro_fed():
    fed_epoch = 20
    device_num = 6
    layer_num = 3

    model_path = './model/bert-base-uncased/'
    file_path = './data/datasets/Biology/'
    param_dict = './outputs/LayerModel/Biology/NewPro_0-11/'

    name_list = natsort.natsorted(os.listdir(file_path), alg=natsort.ns.PATH)  # 各个client的训练语料
    param_container = utils.create_container()  # 制作本地参数容器

    model_list = []  # 记录各个客户端的参数
    for i in range(device_num):
        # layer_num = random.randint(3, 7)  # 产生模型架构层数，3-6之间

        print("模型transformer层数为：%d" % layer_num)

        modelConfig = BertConfig.from_pretrained(model_path)
        modelConfig.num_hidden_layers = layer_num  # 相当于构建一个小模型，transformer层只有六层
        model = BertForMaskedLM.from_pretrained(model_path, config=modelConfig)

        model_list.append(model)

    for i in range(fed_epoch):
        # 记录本轮联邦存储的位置，如果文件夹不存在，则进行文件夹的创建
        epoch_save = param_dict + 'epoch_' + str(i + 1) + '/'
        if not os.path.exists(epoch_save):
            os.makedirs(epoch_save)

        change_flag = True

        if i == 0:
            layer_list = [0, 1, 2]
            change_flag = False
        elif i == 5:
            layer_list = [3, 4, 5]
            change_flag = False
        elif i == 10:
            layer_list = [6, 7, 8]
            change_flag = False
        elif i == 15:
            layer_list = [9, 10, 11]
            change_flag = False

        for j in range(device_num):
            print("%d轮联邦%d号设备训练中------" % (i + 1, j))
            param_save = epoch_save + 'client_' + str(j) + '.pt'
            param_read = param_dict + 'epoch_' + str(i) + '/fed_avg.pt'

            # 映射为当前想要训练的模型层
            model_list[j] = utils.map3to12(model_list[j], layer_list, param_container)

            if change_flag:
                # 如果不是第一轮联邦训练，则更新模型之前训练得到的参数
                param_container = utils.update_container(param_container, param_read)
                model_list[j] = utils.re_param(model_list[j], param_read)

            model_list[j] = utils.train_trans_layer(model_list[j], [0, 1, 2])  # 只训练transformers层的第i层
            #
            model_list[j] = dp_pretrain(learning_rate=5e-5, epochs=1, batch_size=256,
                                        model=model_list[j], file_path=file_path + name_list[j])

            # 保存client更新的参数
            utils.layer_save(model_list[j], param_save)

        # 进行联邦聚合
        utils.federated_efficient_merge(epoch_save)


def fed_train():
    fed_epoch = 5
    device_num = 6
    layer_num = 8

    domain = 'Computer'

    model_path = './model/bert-base-uncased/'
    file_path = './data/datasets/'+domain+'/'
    param_dict = './outputs/LayerModel/Ablation/'+domain+'/Pro3_8_e5/'

    name_list = natsort.natsorted(os.listdir(file_path), alg=natsort.ns.PATH)  # 各个client的训练语料
    param_container = utils.create_container()  # 制作本地参数容器

    model_list = []  # 记录各个客户端的参数
    for i in range(device_num):
        # layer_num = random.randint(3, 7)  # 产生模型架构层数，3-6之间

        print("模型transformer层数为：%d" % layer_num)

        modelConfig = BertConfig.from_pretrained(model_path)
        modelConfig.num_hidden_layers = layer_num  # 相当于构建一个小模型，transformer层只有六层
        model = BertForMaskedLM.from_pretrained(model_path, config=modelConfig)
        # model = utils.map9to3(model)  # 平均高层

        model_list.append(model)

    for i in range(fed_epoch):
        # 记录本轮联邦存储的位置，如果文件夹不存在，则进行文件夹的创建
        epoch_save = param_dict + 'epoch_' + str(i + 1) + '/'
        if not os.path.exists(epoch_save):
            os.makedirs(epoch_save)

        if i < 3:
            drop_layer = 1
        elif i < 4:
            drop_layer = 2
        else:
            drop_layer = 3
        # drop_layer = 1

        for j in range(device_num):
            print("%d轮联邦%d号设备训练中------" % (i + 1, j))

            param_save = epoch_save + 'client_' + str(j) + '.pt'
            param_read = param_dict + 'epoch_' + str(i) + '/fed_avg.pt'

            if i != 0:
                # 如果不是第一轮联邦训练，则更新模型之前训练聚合得到的参数
                param_container = utils.update_container(param_container, param_read)
                model_list[j] = utils.re_param(model_list[j], param_read)

            for e in range(1):
                # 在本地进行训练，每次训练都进行重新构建后续参数
                # 每一轮都新构建一下小模型后续层的参数
                # if i == 0 or i == 3 or i == 4:
                #     #  每轮换层时才更改mapping
                model_list[j] = utils.rebuild_model(model_list[j], param_container, layer_length=layer_num - drop_layer,
                                                    drop_layer=drop_layer, ori_layer=drop_layer - 1)
                if e > 0:
                    # 记录上次训练结果
                    model_list[j] = utils.re_param(model_list[j], param_save)
                model_list[j] = utils.train_trans_layer(model_list[j], [drop_layer - 1])  # 只训练transformers层的第i层
                model_list[j] = utils.train_cls_layer(model_list[j])  # 训练分类层

                # 在further pretrain中重构模型的后续层
                model_list[j] = dp_pretrain(learning_rate=5e-5, epochs=1, batch_size=256,
                                            model=model_list[j], file_path=file_path + name_list[j])

                # 保存client更新的参数
                utils.layer_save(model_list[j], param_save)

                # 更新客户端本地训练参数
                # param_container = utils.update_container(param_container, param_save)
                # model_list[j] = utils.re_param(model_list[j], param_save)

        # print("测试第%d轮联邦后训练结果：" % (i + 1))

        # 进行联邦聚合
        utils.federated_efficient_merge(epoch_save)


def center_train():
    domain = 'Computer'

    model_path = './model/bert-base-uncased/'
    file_path = './data/datasets/Center/' + domain + '_128.pt'
    param_dict = './outputs/LayerModel/' + domain + '/Bert_center/'
    # param_save = './outputs/LayerModel/Center/Biology_higher_e5.pt'

    center_epoch = 5
    # layer_num = 6

    modelConfig = BertConfig.from_pretrained(model_path)
    # modelConfig.num_hidden_layers = layer_num
    model = BertForMaskedLM.from_pretrained(model_path, config=modelConfig)

    # model = utils.map9to3(model)  # 平均高层参数

    # param_container = utils.create_container()  # 制作本地参数容器

    for i in range(center_epoch):
        epoch_save = param_dict + 'epoch_' + str(i + 1) + '/'
        if not os.path.exists(epoch_save):
            os.makedirs(epoch_save)

        # if i < 3:
        #     drop_layer = 1
        # elif i < 4:
        #     drop_layer = 2
        # else:
        #     drop_layer = 3

        param_save = epoch_save + 'layer.pt'
        param_read = param_dict + 'epoch_' + str(i) + '/layer.pt'

        # model = utils.rebuild_model(model, param_container, layer_length=layer_num - drop_layer,
        #                             drop_layer=drop_layer, ori_layer=drop_layer - 1)

        if i > 0:
            model = utils.re_param(model, param_read)
        # model = utils.train_trans_layer(model, [drop_layer - 1])  # 只训练transformers层的第i层

        for name, params in model.named_parameters():
            if params.requires_grad:
                print("True:" + name)
        print("----------------------------")

        model = dp_pretrain(learning_rate=5e-5, epochs=1, batch_size=256,
                            model=model, file_path=file_path)

        utils.layer_save(model, param_save)

        # 更新参数
        # param_container = utils.update_container(param_container, param_save)


def layer_train():
    layers = 6
    model_path = './model/bert-base-uncased/'
    file_path = './data/datasets/Center/Biology_128.pt'
    param_save = './outputs/params/Center/Layers/'

    modelConfig = BertConfig.from_pretrained(model_path)

    for i in range(layers):
        print("Layer %d is training------" % i)
        save_name = 'layer_' + str(i) + '.pt'

        model = BertForMaskedLM.from_pretrained(model_path, config=modelConfig)
        model = utils.train_trans_layer(model, [i])

        model = dp_pretrain(learning_rate=5e-5, epochs=1, batch_size=256,
                            model=model, file_path=file_path)

        utils.layer_save(model, param_save + save_name)


def traditional_FL():
    fed_epoch = 5
    device_num = 6

    model_path = './model/bert-base-uncased/'
    file_path = './data/datasets/Computer/'
    param_dict = './outputs/LayerModel/Computer/Bert_FL/'

    name_list = natsort.natsorted(os.listdir(file_path), alg=natsort.ns.PATH)  # 各个client的训练语料

    model_list = []  # 记录各个客户端的参数
    for i in range(device_num):

        modelConfig = BertConfig.from_pretrained(model_path)
        model = BertForMaskedLM.from_pretrained(model_path, config=modelConfig)
        # model = utils.map9to3(model)  # 平均高层

        model_list.append(model)

    for i in range(fed_epoch):
        # 记录本轮联邦存储的位置，如果文件夹不存在，则进行文件夹的创建
        epoch_save = param_dict + 'epoch_' + str(i + 1) + '/'
        if not os.path.exists(epoch_save):
            os.makedirs(epoch_save)

        for j in range(device_num):
            print("%d轮联邦%d号设备训练中------" % (i + 1, j))

            param_save = epoch_save + 'client_' + str(j) + '.pt'
            param_read = param_dict + 'epoch_' + str(i) + '/fed_avg.pt'

            if i != 0:
                # 如果不是第一轮联邦训练，则更新模型之前训练聚合得到的参数
                model_list[j] = utils.re_param(model_list[j], param_read)

            model_list[j] = dp_pretrain(learning_rate=5e-5, epochs=1, batch_size=256,
                                        model=model_list[j], file_path=file_path + name_list[j])

            # 保存client更新的参数
            utils.layer_save(model_list[j], param_save)

        # 进行联邦聚合
        utils.federated_efficient_merge(epoch_save)


def main():
    fed_train()
    # center_train()
    # rebuild_test()
    # update_test()
    # layer_train()
    # pro_fed()
    # traditional_FL()


if __name__ == "__main__":
    main()
