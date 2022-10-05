import torch
from functools import partial
from megatron import get_args, get_tokenizer, mpu
from megatron.utils import get_ltor_masks_and_position_ids

# def get_batch_pipe_teacher(data, teacher_model):
#     args = get_args()
#     tokenizer = get_tokenizer()

#     # Items and their type.
#     keys = ['text']
#     datatype = torch.int64

#     print(next(data))

#     # Broadcast data.
#     data_b = mpu.broadcast_data(keys, data, datatype)

#     # Unpack.
#     tokens_ = data_b['text'].long()
#     tokens = tokens_[:, :-1].contiguous()

#     # Get the masks and position ids.
#     attention_mask, _, position_ids = get_ltor_masks_and_position_ids(
#         tokens,
#         tokenizer.eod,
#         args.reset_position_ids,
#         args.reset_attention_mask,
#         args.eod_mask_loss,
#         prefix_indices=None,
#         loss_on_targets_only=args.loss_on_targets_only
#     )

#     teacher_logits = teacher_model[0].eval_batch(list((tokens, position_ids, attention_mask)), compute_loss = False, reduce_output = None)
#     return teacher_logits

def get_batch_pipe_student(data, teacher_model):
    """Modification of `get_batch` to work on `next(data_iterator)` instead of `data_iterator`"""
    args = get_args()
    tokenizer = get_tokenizer()
    # print("before eval batch 0")


    # Items and their type.
    keys = ['text']
    datatype = torch.int64
    # print("before eval batch 1")

    # Broadcast data.
    data_b = mpu.broadcast_data(keys, data, datatype)
    # print("before eval batch 2")

    # Unpack.
    tokens_ = data_b['text'].long()
    labels = tokens_[:, 1:].contiguous()
    tokens = tokens_[:, :-1].contiguous()
    
    #print("before eval batch 3")
    # Get the masks and position ids.
    attention_mask, loss_mask, position_ids = get_ltor_masks_and_position_ids(
        tokens,
        tokenizer.eod,
        args.reset_position_ids,
        args.reset_attention_mask,
        args.eod_mask_loss,
        prefix_indices=None,
        loss_on_targets_only=args.loss_on_targets_only
    )
    # print("before eval batch 4∏")
    teacher_logits = teacher_model[0].eval_batch(iter(list((tokens, position_ids, attention_mask))), compute_loss = False, reduce_output = None)


    
    if args.curriculum_learning and args.curriculum_seqlen < tokens.size()[1]:
        # seqlen-based curriculum learning
        # tokens, position_ids, labels, loss_mask have size [batch size, seqlen]
        tokens = tokens[:, :args.curriculum_seqlen].contiguous()
        position_ids = position_ids[:, :args.curriculum_seqlen].contiguous()
        labels = labels[:, :args.curriculum_seqlen].contiguous()
        loss_mask = loss_mask[:, :args.curriculum_seqlen].contiguous()

    return (tokens, position_ids, attention_mask), (labels, loss_mask, teacher_logits)