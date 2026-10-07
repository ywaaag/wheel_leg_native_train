"""Single locked attempt ledger; all mutations address one exact attempt ID."""
import fcntl
import json
import os
from pathlib import Path
import time

PHASE_COUNTER = {"smoke":"smoke", "formal":"formal"}


class Ledger:
    def __init__(self, path):
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(".lock")

    def _change(self, operation):
        with self.lock_path.open("a+") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            data = json.loads(self.path.read_text())
            result = operation(data)
            temporary = self.path.with_name(self.path.name+f".{os.getpid()}.tmp")
            temporary.write_text(json.dumps(data,indent=2)+"\n")
            os.replace(temporary,self.path)
            return result

    def reserve(self, attempt_id, phase, output_dir):
        output = str(Path(output_dir).resolve())
        def change(book):
            if book.get("authorization")!="AUTHORIZED":
                raise ValueError("new simulation/PPO budget has not been authorized")
            if phase not in book["limits"] or attempt_id in book["attempts"]:
                raise ValueError("unknown phase or duplicate attempt ID")
            if any(row["output_dir"]==output for row in book["attempts"].values()):
                raise ValueError("output path already reserved")
            if any(row["status"]=="RUNNING" for row in book["attempts"].values()):
                raise ValueError("another attempt is running")
            if book["used"][phase] >= book["limits"][phase]:
                raise ValueError("phase budget exhausted")
            completed = {name for name in book["limits"] if any(
                row["phase"]==name and row["status"]=="COMPLETED"
                for row in book["attempts"].values())}
            spec=json.loads(self.path.with_name('spec.json').read_text())
            if phase=='formal':
                from native_stand.command_v6.wiring import completed_smoke
                completed.discard('smoke')
                if completed_smoke(book,spec):completed.add('smoke')
            initialization=json.loads(self.path.with_name('spec.json').read_text()).get('initialization','warmstart') if self.path.with_name('spec.json').is_file() else 'warmstart'
            recovery_ready=bool(json.loads(self.path.with_name('spec.json').read_text()).get('recovery',{}).get('runtime_initialization_validated')) if self.path.with_name('spec.json').is_file() else False
            # Checkpoint evaluation is an independent read-only phase; it does
            # not require a fresh source-eval attempt in the same ledger.
            retention=bool(json.loads(self.path.with_name('spec.json').read_text()).get('retention',{}).get('enabled')) if self.path.with_name('spec.json').is_file() else False
            prerequisites={"smoke":set() if initialization=='random' or recovery_ready or retention else {"source_eval"},"formal":{"smoke"},
                           "evaluate":set(),"play":{"source_eval"}}
            if not prerequisites.get(phase,set()) <= completed:
                raise ValueError("required preceding phase has not completed")
            book["attempts"][attempt_id] = {"phase":phase,"output_dir":output,
                "status":"RUNNING","updates":0,"started_unix_s":time.time()}
        self._change(change)


    def charge(self, attempt_id, output_dir):
        output = str(Path(output_dir).resolve())
        def change(book):
            row = book["attempts"].get(attempt_id)
            if row is None or row["output_dir"] != output or row["status"] != "RUNNING":
                raise ValueError("attempt identity, path or running state differs")
            phase = row["phase"]
            if phase in ("source_eval","evaluate","play"):
                raise ValueError("source-only evaluation or playback has no PPO updates")
            if book["used"][phase] >= book["limits"][phase]:
                raise ValueError("phase budget exhausted")
            row["updates"] += 1
            book["used"][phase] += 1
            return row["updates"]
        return self._change(change)

    def finalize(self, attempt_id, output_dir, status, *, exit_code=None, reason=None, wall_s=None):
        output = str(Path(output_dir).resolve())
        if status not in ("COMPLETED","FAILED","STOPPED_BOUNDED","TERMINATED","UNKNOWN"):
            raise ValueError("invalid terminal status")
        def change(book):
            row = book["attempts"].get(attempt_id)
            if row is None or row["output_dir"] != output or row["status"] != "RUNNING":
                raise ValueError("attempt already ended or identity differs")
            row.update(status=status, exit_code=exit_code, reason=reason,
                       finished_unix_s=time.time(),wall_s=wall_s)
            if row["phase"] in ("source_eval","evaluate","play"):
                book["used"][row["phase"]] += 1
            if row["phase"] == "source_eval":
                if wall_s is not None:
                    book["source_eval_wall_used_s"] += wall_s
        self._change(change)

def transfer_unused_updates(old_path, new_path, new_book, *, transfer_id, requested, smoke_updates=5):
    """Locked quota transfer; preserve ended attempts and provide crash recovery."""
    old_path,new_path=Path(old_path).resolve(),Path(new_path).resolve()
    new_path.parent.mkdir(parents=True,exist_ok=True)
    with old_path.with_suffix('.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        old=json.loads(old_path.read_text())
        transfers=old.setdefault('quota_transfers',{})
        if transfer_id in transfers:
            record=transfers[transfer_id]
            if record['destination']!=str(new_path):
                raise ValueError('transfer identity destination differs')
            if not new_path.exists():
                temporary=new_path.with_suffix('.recover.tmp')
                temporary.write_text(json.dumps(record['initial_destination_ledger'],indent=2)+'\n')
                os.replace(temporary,new_path)
            return record['updates']
        if new_path.exists() or any(x['status']=='RUNNING' for x in old['attempts'].values()):
            raise ValueError('destination exists or source budget occupied')
        available=old['limits']['formal']-old['used']['formal']
        amount=min(available,requested)
        if not isinstance(smoke_updates,int) or smoke_updates<1 or amount<smoke_updates+1:
            raise ValueError('insufficient unused updates for smoke and formal')
        new_book['limits']['smoke']=smoke_updates
        new_book['limits']['formal']=amount-new_book['limits']['smoke']
        new_book['quota_origin']={'ledger':str(old_path),'transfer_id':transfer_id,
                                  'updates':amount,'no_additional_updates':True}
        old['limits']['formal']-=amount
        transfers[transfer_id]={'destination':str(new_path),'updates':amount,
            'time_unix_s':time.time(),'initial_destination_ledger':new_book}
        # Source debit precedes destination publication. The recorded immutable initial
        # ledger is sufficient to recover publication without charging a second time.
        temporary=old_path.with_suffix('.transfer.tmp')
        temporary.write_text(json.dumps(old,indent=2)+'\n')
        os.replace(temporary,old_path)
        temporary=new_path.with_suffix('.transfer.tmp')
        temporary.write_text(json.dumps(new_book,indent=2)+'\n')
        os.replace(temporary,new_path)
        return amount
