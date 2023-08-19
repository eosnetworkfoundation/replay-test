# a dictionary that holds job status
# primary key is an integer `job_id`
# `replay_slice_id` integer FK linked to `replay-configuration` pk of same name
# `status` enum of waiting_4_worker, started, working, finished, error, timeout
# `last_block_processed` block id of last block processed
# `start_time` date time job started
# `end_time` date time job completed
# `actual_integrity_hash` hash once last block has been reached
