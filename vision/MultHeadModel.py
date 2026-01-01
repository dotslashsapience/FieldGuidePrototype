from fastai.vision.all import *
import pandas
import fastcore

# TARGET CER < 0.5%: CER = N_wrg_acpt/N_acpt
# df columns: fname, species, usable
# species can be string labels; fastai will map them to indices automatically via CategoryBlock.

dblock = DataBlock(
    blocks=(ImageBlock, (CategoryBlock, TransformBlock)),
    get_x=ColReader("fname"),
    get_y=lambda r: (r["species"], float(r["usable"])),  # (class, 0/1 float)
    splitter=RandomSplitter(valid_pct=0.2, seed=42),
    item_tfms=Resize(256),
    batch_tfms=[*aug_transforms(size=224), Normalize.from_stats(*imagenet_stats)],
)

dls = dblock.dataloaders(df, bs=64)

import torch
import torch.nn as nn
from fastai.vision.all import create_timm_model


class MultiHeadNet(nn.Module):
    def __init__(self, arch: str, n_species: int):
        super().__init__()
        # Create a timm model with no classifier head (num_classes=0 makes it a feature extractor in many timm models)
        self.backbone = create_timm_model(arch, n_out=0, pretrained=True)

        # Need feature dimension of backbone output:
        # create_timm_model returns a fastai-wrapped model; easiest is to infer with a dummy forward.
        with torch.no_grad():
            dummy = torch.zeros(1, 3, 224, 224)
            feats = self.backbone(dummy)
            feat_dim = feats.shape[-1]

        self.head_species = nn.Linear(feat_dim, n_species)  # 4000 logits
        self.head_triage = nn.Linear(feat_dim, 1)  # 1 logit (usable)

    def forward(self, x):
        feats = self.backbone(x)
        species_logits = self.head_species(feats)
        triage_logit = self.head_triage(feats).squeeze(-1)  # (bs,)
        return species_logits, triage_logit


class MultiLoss(nn.Module):
    def __init__(self, triage_weight: float = 0.1):
        super().__init__()
        self.triage_weight = triage_weight
        self.ce = CrossEntropyLossFlat()
        self.bce = BCEWithLogitsLossFlat()

    def forward(self, preds, targs):
        species_logits, triage_logit = preds
        y_species, y_usable = targs  # y_species: (bs,), y_usable: (bs,)

        loss_species = self.ce(species_logits, y_species)
        loss_triage = self.bce(triage_logit, y_usable.float())
        return loss_species + self.triage_weight * loss_triage


def triage_acc(preds, targs):
    _, triage_logit = preds
    _, y_usable = targs
    pred = (triage_logit.sigmoid() >= 0.5).float()
    return (pred == y_usable.float()).float().mean()


def species_acc(preds, targs):
    species_logits, _ = preds
    y_species, _ = targs
    return accuracy(species_logits, y_species)


def species_top5(preds, targs):
    species_logits, _ = preds
    y_species, _ = targs
    return top_k_accuracy(species_logits, y_species, k=5)


arch = "convnext_small"  # timm name; verify yours
n_species = len(dls.vocab[0])  # CategoryBlock vocab for species

model = MultiHeadNet(arch=arch, n_species=n_species)
loss_func = MultiLoss(triage_weight=0.1)

learn = Learner(
    dls, model, loss_func=loss_func, metrics=[species_acc, species_top5, triage_acc]
).to_fp16()

learn.fine_tune(5, base_lr=1e-3)


"""Below is a folder based label implementation."""

from fastai.vision.all import *
import pandas as pd
from pathlib import Path

path = Path("/path/to/dataset")  # contains subfolders per species

# Collect image files and their species labels from folder names
files = get_image_files(path)
species = [f.parent.name for f in files]  # folder name label

# triage labels: map filename -> usable (0/1)
# tri_df must have columns: fname, usable
tri_df = pd.read_csv(path / "triage_labels.csv")

# Build a df that fastai can use
df = pd.DataFrame({"fname": files, "species": species})

# Join triage labels by filename (choose a stable key!)
# If tri_df stores just the basename:
df["key"] = df["fname"].map(lambda p: Path(p).name)
tri_df["key"] = tri_df["fname"].map(lambda p: Path(p).name)

df = df.merge(tri_df[["key", "usable"]], on="key", how="inner")

# Sanity check
assert df["usable"].isin([0, 1]).all()

df["key"] = df["fname"].map(lambda p: str(Path(p).relative_to(path)))
tri_df["key"] = tri_df["fname"].astype(str)
df = df.merge(tri_df[["key", "usable"]], on="key", how="inner")


dblock = DataBlock(
    blocks=(ImageBlock, (CategoryBlock, TransformBlock)),
    get_x=ColReader("fname"),
    get_y=lambda r: (r["species"], float(r["usable"])),
    splitter=RandomSplitter(valid_pct=0.2, seed=42),
    item_tfms=Resize(256),
    batch_tfms=[*aug_transforms(size=224), Normalize.from_stats(*imagenet_stats)],
)

dls = dblock.dataloaders(df, bs=64)


import torch
import torch.nn as nn
from fastai.vision.all import create_timm_model


class MultiHeadNet(nn.Module):
    def __init__(self, arch: str, n_species: int):
        super().__init__()
        self.backbone = create_timm_model(arch, n_out=0, pretrained=True)

        with torch.no_grad():
            dummy = torch.zeros(1, 3, 224, 224)
            feat_dim = self.backbone(dummy).shape[-1]

        self.head_species = nn.Linear(feat_dim, n_species)
        self.head_triage = nn.Linear(feat_dim, 1)

    def forward(self, x):
        feats = self.backbone(x)
        species_logits = self.head_species(feats)
        triage_logit = self.head_triage(feats).squeeze(-1)
        return species_logits, triage_logit


class MultiLoss(nn.Module):
    def __init__(self, triage_weight: float = 0.1):
        super().__init__()
        self.triage_weight = triage_weight
        self.ce = CrossEntropyLossFlat()
        self.bce = BCEWithLogitsLossFlat()

    def forward(self, preds, targs):
        species_logits, triage_logit = preds
        y_species, y_usable = targs
        loss_species = self.ce(species_logits, y_species)
        loss_triage = self.bce(triage_logit, y_usable.float())
        return loss_species + self.triage_weight * loss_triage


def triage_acc(preds, targs):
    _, triage_logit = preds
    _, y_usable = targs
    pred = (triage_logit.sigmoid() >= 0.5).float()
    return (pred == y_usable.float()).float().mean()


def species_acc(preds, targs):
    species_logits, _ = preds
    y_species, _ = targs
    return accuracy(species_logits, y_species)


def species_top5(preds, targs):
    species_logits, _ = preds
    y_species, _ = targs
    return top_k_accuracy(species_logits, y_species, k=5)


arch = "convnext_small"  # timm model name
n_species = len(dls.vocab[0])

model = MultiHeadNet(arch, n_species)
learn = Learner(
    dls,
    model,
    loss_func=MultiLoss(triage_weight=0.1),
    metrics=[species_acc, species_top5, triage_acc],
).to_fp16()

learn.fine_tune(5, base_lr=1e-3)
