#!/bin/bash
# Fetch "Session Handoff — Active" from Apple Notes "Claude 工作區"
# Used by Claude Code SessionStart hook to inject handoff context automatically.

osascript -e '
tell application "Notes"
    set targetFolder to folder "Claude 工作區" of account "iCloud"
    set allNotes to notes of targetFolder
    repeat with aNote in allNotes
        if name of aNote is "Session Handoff — Active" then
            set noteText to plaintext of aNote
            set modDate to modification date of aNote
            if length of noteText > 2500 then
                set noteText to text 1 thru 2500 of noteText & return & "[truncated]"
            end if
            return "Session Handoff — Active (updated: " & modDate & "):" & return & noteText
        end if
    end repeat
    return "Claude 工作區沒有 Session Handoff — Active 筆記"
end tell
'
