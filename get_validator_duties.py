import json
import math
from datetime import datetime, timedelta

import requests


SLOTS_PER_EPOCH = 32
SECONDS_PER_SLOT = 12


def main(validators_indices, eth2_api_url="http://localhost:5052/eth/v1/"):
    def api_get(endpoint):
        return requests.get(f"{eth2_api_url}{endpoint}").json()

    def api_post(endpoint, data2):
        headers = {'Content-type': 'application/json'}
        print(data2)
        k = requests.post(f"{eth2_api_url}{endpoint}", data=data2, headers=headers)
        print(k)
        return k.json()

    head_slot = int(api_get("beacon/headers/head")["data"]["header"]["message"]["slot"])
    epoch = head_slot // SLOTS_PER_EPOCH
    epoch = int(api_get("beacon/states/head/finality_checkpoints")["data"]["finalized"]["epoch"])
    epoch = epoch + 2
    print(epoch)
    print("indices")
    str_indices = ["12345"]
    print(str_indices)
    cur_epoch_data = api_post(f"validator/duties/attester/{epoch}", json.dumps(str_indices))["data"]
    next_epoch_data = api_post(
        f"validator/duties/attester/{epoch + 1}", json.dumps(str_indices)
    )["data"]

    genesis_timestamp = 1606824023
    print(cur_epoch_data)
    print(next_epoch_data)
    attestation_duties = {}
    for d in (*cur_epoch_data, *next_epoch_data):
        print(d)
        print(d['slot'])
        attestation_duties.setdefault(int(d['slot']), []).append(d['validator_index'])
    attestation_duties = {k: v for k, v in sorted(attestation_duties.items()) if k > head_slot}

    # Also insert (still unknown) attestation duties at epoch after next,
    # assuming worst case of having to attest at its first slot
    first_slot_epoch_p2 = (epoch + 2) * SLOTS_PER_EPOCH
    attestation_duties[first_slot_epoch_p2] = []
    
    print(f"Calculating attestation slots and gaps for validators:")
    print(f"  {validators_indices}")
    print(attestation_duties)
    print("\nUpcoming voting slots and gaps")
    print("(Gap in seconds)")
    print("(slot/epoch - time range - validators)")
    print("*" * 80)

    prev_end_time = datetime.now()
    longest_gap = timedelta(seconds=0)
    gap_time_range = (None, None)

    for slot, validators in attestation_duties.items():
        slot_start = datetime.fromtimestamp(genesis_timestamp + slot * SECONDS_PER_SLOT)
        slot_end = slot_start + timedelta(seconds=SECONDS_PER_SLOT)
        print(slot_start)
        print(slot_end)
        print("slot end")
        print(prev_end_time)
        gap = slot_start - prev_end_time
        print(f"Gap - {math.floor((slot_start - prev_end_time).total_seconds())} seconds")

        if validators:
            print(
                f"  {slot}/{slot // SLOTS_PER_EPOCH}"
                f" - {slot_start.strftime('%H:%M:%S')} until {slot_end.strftime('%H:%M:%S')}"
                f" - [{', '.join(validators)}]"
            )
        else:
            assert slot % SLOTS_PER_EPOCH == 0

        if gap > longest_gap:
            longest_gap = gap
            gap_time_range = (prev_end_time, slot_start)

        prev_end_time = slot_end

    print("\nLongest gap (first):")
    print("*" * 80)
    print(
        f"{longest_gap.total_seconds()} seconds"
        f" ({int(longest_gap.total_seconds()) // SECONDS_PER_SLOT} slots),"
        f" from {gap_time_range[0].strftime('%H:%M:%S')}"
        f" until {gap_time_range[1].strftime('%H:%M:%S')}"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Show validator duties of current and next epoch to find largest gap."
    )
    parser.add_argument("indices", metavar="index", type=int, nargs="+", help="validator indices")

    args = parser.parse_args()

    main(args.indices)
