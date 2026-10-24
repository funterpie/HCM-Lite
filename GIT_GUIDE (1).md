# GIT GUIDE v2: everything about collaborating on GitHub (push, pull, existing work, conflicts, fixes)

Repo: https://github.com/funterpie/HCM-Lite.git
Read sections 0 to 6 once. Keep sections 8 to 12 open during the build.

---

## 0. The 6 rules (if you read nothing else)

1. **One repo.** `main` is what gets deployed. Render and Vercel build from `main`.
2. **Each person works on their own branch:** `taha/work`, `saqib/work`, `abdullah/work`, `farhan/work`.
3. **Only edit files you own** (see your personal `.md`). That keeps merges clean.
4. **Pull before you start, merge after every finished task** (at least every 30 minutes), then say "merged T#" in the team chat.
5. **Never force-push. Never commit `.env`, keys, `.venv/`, `node_modules/`.**
6. **If a teammate hasn't pushed what you need, use a stub** (section 8). Never wait, never write their part.

---

## 1. One-time setup on your laptop (everyone, 5 minutes)

```bash
git --version                                   # if missing: install Git (git-scm.com)
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
git config --global pull.rebase false           # avoids the "divergent branches" prompt; pull = merge
```

**Log in to GitHub from the terminal.** GitHub does not accept your account password for git over HTTPS. Use one of:
- Git for Windows / macOS: when `git clone` or `git push` asks, sign in through the **browser window** that opens (Git Credential Manager).
- Or the GitHub CLI: `gh auth login`
- Or a **personal access token** (GitHub, Settings, Developer settings, Personal access tokens) with repo access, pasted when it asks for a password.

**Accept the invitation.** Check your email, or open https://github.com/funterpie/HCM-Lite/invitations. If you skip this, every push fails with "Permission denied / 403".

**Test access:**
```bash
git clone https://github.com/funterpie/HCM-Lite.git
```
GUI alternative: GitHub Desktop or the VS Code Source Control panel do the same steps with buttons. The rules above still apply.

---

## 2. Taha's first push (once, only if `main` is still empty)

If someone else already pushed to `main`, skip this and do section 3 instead.

```bash
git clone https://github.com/funterpie/HCM-Lite.git
cd HCM-Lite
# copy in: PROJECT.md, FINAL_GUIDE.md, GIT_GUIDE.md, SAQIB.md, TAHA.md, ABDULLAH.md, FARHAN.md, guides/, supabase/schema.sql
mkdir -p backend frontend progress
printf ".env\n.venv/\n__pycache__/\nnode_modules/\ndist/\n*.pyc\n.DS_Store\n" > .gitignore
touch backend/.gitkeep frontend/.gitkeep progress/.gitkeep
git add .
git commit -m "chore: project files and guides"
git push origin main
```
Then tell the team: "repo is up, clone and create your branch".

If the push is rejected because `main` already has commits: `git pull origin main`, then `git push origin main`.

---

## 3. Everyone else: clone and make your branch

```bash
git clone https://github.com/funterpie/HCM-Lite.git
cd HCM-Lite
git checkout -b saqib/work            # use YOUR name: taha/work, abdullah/work, farhan/work
git push -u origin saqib/work
```
Already cloned earlier? `git checkout main && git pull origin main`, then create or switch to your branch.

---

## 4. Which folders you are allowed to touch

| Person | Folders and files |
|---|---|
| Taha | `backend/app/main.py`, `core/`, `db.py`, `supabase/`, `modules/{auth,settings,employees,comms}`, `modules/payroll/{router,service,repo,schemas}.py`, `modules/dashboards/repo.py` |
| Saqib | `backend/app/rules/`, `modules/{attendance,leave}`, `backend/tests/` |
| Abdullah | `modules/ai/`, `modules/users/`, `modules/dashboards/{router,service,schemas}.py`, `modules/payroll/pdf.py`, `backend/scripts/`, `README.md` |
| Farhan | `frontend/` |
| Anyone | your own `progress/<NAME>.txt` |

Shared files that need care: `requirements.txt` (add lines, never delete others'), `.env.example` (add lines), `PROJECT.md` (change only after telling the team).

---

## 5. Already built code before the repo was ready? (Saqib, Abdullah, anyone) <- READ THIS

Your work sits on your laptop (or in another repo). Bring it into the shared repo like this. **Option A is the one to use.**

### Option A (recommended): copy your files into the shared repo
```bash
git clone https://github.com/funterpie/HCM-Lite.git      # skip if you already cloned
cd HCM-Lite
git checkout -b saqib/work                                # or: git checkout saqib/work  (if the branch already exists)
git pull origin main                                      # get Taha's skeleton and core first
```
Now copy your files into the folders from section 4. Example for Saqib: your rules into `backend/app/rules/`, attendance into `backend/app/modules/attendance/`, leave into `backend/app/modules/leave/`, tests into `backend/tests/`. Abdullah: AI into `backend/app/modules/ai/`, HR logins into `modules/users/`, PDF into `modules/payroll/pdf.py`, scripts into `backend/scripts/`.

**Do NOT copy over** `main.py`, `db.py`, `core/*`, `.env`, `.venv/`, `node_modules/`, or your own `requirements.txt`. Those belong to Taha or stay local. Instead:
- Add your packages as new lines at the end of the shared `backend/requirements.txt`.
- If your code has its own config, DB connection or auth helper, change it to import Taha's (`core.deps`, `db.get_session`) once his code is on `main`. Until then keep your version in a file inside your own module and mark it `# TODO use core`.
- Do not paste real keys into any file. Use environment variables and add the names to `.env.example`.

Then commit and push:
```bash
git status                       # only your files, and NO .env
git add backend/app/rules backend/app/modules/attendance backend/app/modules/leave backend/tests   # your folders
git commit -m "S1-S9: rules, attendance, leave (existing work)"
git push -u origin saqib/work
```
Merge to `main` (section 6, step E) once the code at least imports without errors. Post in chat what you pushed and which task IDs it covers, and update `progress/<NAME>.txt`.

### Option B (advanced, only if your project already has the same folder layout)
Your history is kept, but it can pull a different root structure into the repo. If your layout is not exactly `backend/...`, use Option A.
```bash
cd your-existing-project
git remote add hcm https://github.com/funterpie/HCM-Lite.git
git push hcm HEAD:refs/heads/saqib/work
```
Then ask Taha to review the branch before it is merged.

### If your code needs something Taha hasn't pushed yet
Use a stub with the agreed signature (section 8). Do not wait.

### If you are not sure how to do any of this
Push your work to your own branch anyway (copy the files as above), then message Taha. **Taha can merge your pushed branch into `main`** (section 9, "integrator" fallback).

---

## 6. The daily loop (repeat after every task)

```bash
# A. START: get the latest merged work
git checkout saqib/work
git pull origin main            # merges everyone's work into your branch

# B. do the task with your AI tool and test it (the ACCEPT line in your guide)

# C. check only YOUR files changed
git status
git diff --stat
#   AI tools sometimes edit files you don't own. Undo one: git checkout -- path/to/file

# D. commit and push your branch (this is your backup)
git add <your folders>
git commit -m "S5: check-in/check-out"
git push origin saqib/work

# E. merge into main (only if your task passes its ACCEPT check)
git checkout main
git pull origin main
git merge saqib/work
git push origin main
git checkout saqib/work
git merge main                  # keep your branch up to date

# F. post in the team chat: "merged S5 to main"
```

---

## 7. Push and pull explained

| Command | What it does | When |
|---|---|---|
| `git pull origin main` | Brings the latest `main` into the branch you are on | Start of every task, and right before a merge |
| `git push origin saqib/work` | Uploads your branch (backup, others can see it) | After every commit |
| `git push origin main` | Updates the shared `main` (others pull it, Render/Vercel deploy it) | Only after a successful merge and a local test |
| `git fetch origin` | Downloads info without changing your files | To look at what others pushed |

Look at what others have done without changing anything:
```bash
git fetch origin
git branch -r                                   # all remote branches
git log origin/main --oneline -10               # latest merges on main
git log origin/abdullah/work --oneline -5       # someone's branch
git diff HEAD origin/main --stat                # what you don't have yet
```

---

## 8. A teammate hasn't pushed the code you need

Don't wait and don't write their part. Use the agreed signature in `PROJECT.md` section 10.

| Situation | What to do |
|---|---|
| You need Saqib's `rules/` function | Add a stub in your own module with the exact signature and `# TODO`. Delete it after you pull his code. |
| You need Taha's `core/` | Write against `current_user`, `require_role`, `scoped_employee_id`. Pull when `core/` lands (about T+0:35). |
| You need Abdullah's AI or PDF function | Stub with the agreed signature. |
| Farhan needs an endpoint that isn't live | Mocks (`VITE_USE_MOCKS=true`) and the shapes in `PROJECT.md` section 9. |
| Abdullah needs a Taha SQL function | Stub returning fixed sample data. |
| Blocked for 10 minutes | Ask in chat with the exact name. No reply? Stub it and move on. |

Stub pattern (the real code takes over automatically once pulled):
```python
try:
    from app.rules.payroll import compute_payslip
except ImportError:
    from app.modules.payroll.stubs import compute_payslip   # your own stub file, same signature
```
Delete the stub files before the freeze.

---

## 9. When two people merge at the same time, and the "integrator" fallback

- If `git push origin main` says **rejected** (someone merged first): run `git pull origin main`, fix any conflict, then push again. This is normal.
- If someone can't get their merge working, they push their branch (`git push origin <name>/work`) and tell Taha. **Taha merges it for them:**
```bash
git fetch origin
git checkout main && git pull origin main
git merge origin/saqib/work
git push origin main
```
- Don't enable branch protection on GitHub. It would block direct merges.
- Pull requests are fine if you prefer them: open one from `<name>/work` into `main` and **merge your own PR right away**. Don't wait for review.

---

## 10. Merge CONFLICT

1. Stop. Don't force-push.
2. `git status` lists the conflicted files.
3. Your own file: open it, keep your part, delete the `<<<<<<<`, `=======`, `>>>>>>>` lines, then:
```bash
git add <file>
git commit
```
4. Someone else's file: keep **their** version and tell them: `git checkout origin/main -- <file>` (then `git add <file>`).
5. `requirements.txt`, `package.json`, `.env.example`: keep both people's lines.
6. Stuck for 5 minutes: ask Taha or Abdullah. Worst case, copy your changed files somewhere, delete the folder, re-clone, and copy them back.

---

## 11. Undo and rescue

| Problem | Fix |
|---|---|
| Local changes block a pull | `git stash`, then `git pull origin main`, then `git stash pop` |
| Undo edits to one file (not committed) | `git checkout -- <file>` (or `git restore <file>`) |
| Unstage a file | `git restore --staged <file>` |
| Deleted a file by accident | `git checkout origin/main -- <path>` |
| Bad commit already pushed to `main` | `git revert <commit>` then `git push origin main`, and tell the team |
| Committed on the wrong branch (not pushed yet) | `git checkout correct-branch`, then `git cherry-pick <commit>`. Ask Taha before using `git reset --hard`. |
| Not sure which branch you are on | `git branch` (the star marks it). Detached HEAD: `git checkout <name>/work` |
| **Committed `.env` or a key** | If not pushed: `git rm --cached <file>` then commit. **If pushed: treat the key as leaked.** Replace the Groq key (delete and recreate) and reset the exposed Supabase key or database password in the dashboard, then remove the file from git. Do it immediately. |

---

## 12. Common git errors

| Message | Meaning and fix |
|---|---|
| `Permission denied` / `403` / `Repository not found` | You haven't accepted the invite, or you are logged in to the wrong GitHub account. Accept it (section 1), then retry. |
| `rejected ... non-fast-forward` or `fetch first` | `main` moved. `git pull origin main`, then push again. |
| `divergent branches` | Run `git config --global pull.rebase false`, then `git pull origin main`. |
| `refusing to merge unrelated histories` | Your repo was created separately from the remote. Use Option A in section 5. Only as a last resort: `git pull origin main --allow-unrelated-histories`. |
| `error: failed to push` for a file bigger than 100 MB | You committed `venv`, `node_modules` or a dataset. Remove it with `git rm -r --cached <folder>`, add it to `.gitignore`, commit, push. |
| `LF will be replaced by CRLF` | A harmless Windows warning. Ignore it. |
| `src refspec ... does not match any` | You have no commit yet, or the branch name is different. Run `git status` and `git branch`. |

---

## 13. Milestones (must be merged to `main` by these times, from the 4-hour start)

| Time | On `main` |
|---|---|
| Now | Everyone's **existing work** pushed to their branch and merged (section 5) |
| T+0:10 | Taha's skeleton with the module placeholders |
| T+0:35 | Taha's `core/`, Saqib's `rules/` with tests, Farhan's design system |
| T+1:30 | Setup, auth and login: first end-to-end |
| T+2:30 | Attendance, leave, employees, AI chat |
| T+3:15 | **FEATURE FREEZE.** Everything merged; only bug-fix merges after this |
| T+3:45 | Final merge, README done, submit both links |

---

## 14. Farhan and Lovable

Lovable usually syncs to its **own** GitHub repo. Keep that, and also copy its code into `frontend/` of the main repo at **T+1:30, T+2:45 and T+3:15**:
```bash
git checkout farhan/work && git pull origin main
# copy the Lovable repo's src/, package.json, vite config, index.html into frontend/
git add frontend && git commit -m "F: sync frontend from Lovable"
git push origin farhan/work       # then merge to main (section 6, step E)
```
The judges need the real frontend inside the repo you submit.

---

## 15. Cheat sheet

```bash
git status                          # what changed
git diff --stat                     # which files, how much
git pull origin main                # get others' work
git add <paths> && git commit -m "T#: message"
git push origin <name>/work         # back up your branch
git checkout main && git pull origin main && git merge <name>/work && git push origin main
git log --oneline -10               # recent history
git branch -r                       # all remote branches
git checkout -- <file>              # undo changes to ONE file
git revert <commit>                 # undo a pushed commit
```
Commit messages: `T4: setup + auth module` (task id, then a short note).

## 16. Never

- `git push --force`
- Commit `.env`, keys, `.venv/`, `node_modules/`
- Edit a file you don't own, or overwrite `main.py`, `db.py`, `core/*`
- Merge to `main` without running your part once
- Let an AI tool reformat the whole repo
- Wait on a teammate's code instead of stubbing it
