from torch.utils.data import DataLoader
from .samplers import DistributedBatchSampler
from .dataset import *
from .LAMM_benchmark2D_dataset import LAMM_EVAL_2D
from .LAMM_benchmark3D_dataset import LAMM_EVAL_3D, OctaviusEval3dDataset


def collate_fn(batch):
    res = dict()
    keys = batch[0].keys()
    for key in keys:
        res[key] = [data[key] for data in batch]
    return res


def load_data(args):
    data_name = args["models"][args["model"]]["stage1_train_dataset"]
    assert data_name in globals().keys()

    if data_name == "LAMMDataset":
        dataset = LAMMDataset(
            args["data_path"], args["vision_root_path"], args["vision_type"]
        )
    elif data_name == "OctaviusDataset":
        dataset = OctaviusDataset(
            args["data_path_2d"], args["data_path_3d"], args["vision_root_path_2d"],
            args["vision_root_path_3d"], args["loop_2d"], args["loop_3d"],
        )
    else:
        raise ValueError(f"dataset {data_name} not found.")
    
    return dataset


def load_dataset(args):
    """load LAMM datasets

    :param dict args: input arguments
    :return tupe: dataset, dataloader, sampler
    """
    dataset = load_data(args)
    sampler = torch.utils.data.RandomSampler(dataset)
    world_size = torch.distributed.get_world_size()
    rank = torch.distributed.get_rank()
    batch_size = (
        args["world_size"] * args["dschf"].config["train_micro_batch_size_per_gpu"]
    )
    batch_sampler = DistributedBatchSampler(sampler, batch_size, True, rank, world_size)
    dataloader = DataLoader(
        dataset,
        batch_sampler=batch_sampler,
        num_workers=1,
        collate_fn=dataset.collate,
        pin_memory=True,
    )
    return dataset, dataloader, sampler


def load_2Deval_dataset(base_data_path,
                        dataset_name,
                        mode='common',
                        load_data=True,
                        batch_size=1):
    dataset = LAMM_EVAL_2D(base_data_path,
                           dataset_name,
                           mode,
                           load_data)
    dataloader = DataLoader(dataset=dataset, batch_size=batch_size,shuffle=False,num_workers=2, drop_last=False,collate_fn=collate_fn)
    return dataloader


def load_3Deval_dataset(base_data_path,
                        dataset_name,
                        mode='common',
                        load_data=True,
                        batch_size=1):
    dataset = LAMM_EVAL_3D(base_data_path,
                           dataset_name,
                           mode,
                           load_data)
    dataloader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=False, num_workers=2, drop_last=False, collate_fn=collate_fn)
    return dataloader


def load_3Deval_dataset_v2(base_data_path,
                           task_name,
                           dataset_name,
                           vision_root_path,
                           batch_size=1):
    dataset = OctaviusEval3dDataset(
        base_data_path,
        task_name,
        dataset_name, 
        vision_root_path
    )
    dataloader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=False, num_workers=2, drop_last=False, collate_fn=dataset.collate)
    return dataloader
