import torch


class NMEMetric:
    def __init__(self, h: int, w: int) -> None:
        # 两眼外角点对应keypoint索引
        self.keypoint_idxs = [60, 72]
        self.nme_accumulator = 0.
        self.counter = 0.
        self.hw_tensor = torch.as_tensor([h, w]).reshape([1, 1, 2])

    def update(self, pred: torch.Tensor, gt: torch.Tensor, mask: torch.Tensor):
        """
        Args:
            pred (shape [N, K, 2]): pred keypoints
            gt (shape [N, K, 2]): gt keypoints
            mask (shape [N, K]): valid keypoints mask
        """
        dtype = pred.dtype
        device = pred.device

        # rel coord to abs coord
        hw_tensor = self.hw_tensor.to(device=device, dtype=dtype)
        pred = pred * hw_tensor
        gt = gt * hw_tensor
        l2_loss = (pred - gt).pow(2).mean(dim=(1, 2))
        # ion: inter-ocular distance normalized error
        ion = (pred[:, self.keypoint_idxs] - gt[:, self.keypoint_idxs]).pow(2).sum(dim=(1, 2)).pow(0.5)

        valid_ion_mask = ion > 0
        mask = torch.logical_and(mask, valid_ion_mask.unsqueeze_(dim=1))
        num_valid = (mask.sum(dim=1) > 0).sum().item()

        # avoid divide by zero
        ion[ion <= 0] = 1e-6

        self.nme_accumulator += l2_loss.div(ion).sum().item()
        self.counter += num_valid

    def evaluate(self):
        return self.nme_accumulator / self.counter


if __name__ == '__main__':
    metric = NMEMetric()
    metric.update(pred=torch.randn(32, 98, 2),
                  gt=torch.randn(32, 98, 2),
                  mask=torch.randn(32, 98))
    print(metric.evaluate())
