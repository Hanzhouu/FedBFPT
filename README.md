# FedBFPT
In this study, we have built upon previous research to investigate the role of the shallow layer in federated learning (FL) based Bert further pre-training.
To combat the limited computation and communication resources on the client side in FL, we proposed a novel framework, referred to as FedBFPT, which allows for training a single transformer layer of a global Bert model on the client side. Moreover, we proposed the Progressive Learning with Sampled Deep Layers (PL-SDL) method as a means of effectively and efficiently training the local Bert model with a focus on the shallower layers. Through experiments on a variety of corpora across multiple domains, including biology, computer science, and medicine,  we have demonstrated that our proposed FedBFPT in combination with PL-SDL, is capable of achieving accuracy levels comparable to traditional FL methods while significantly reducing computational and communication costs. Details can be seen:
## 1. Environment
1. We suggest you create a Conda environment called "FedBFPT" with Python 3.9 (any version >= 3.6 should work):
```python
conda create -n FedBFPT python=3.9
```
then do
```python
conda activate FedBFPT
```
2.
