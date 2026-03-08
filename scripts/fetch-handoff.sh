#!/bin/bash
# Fetch agent-specific + shared Session Handoff from Apple Notes "Claude 工作區"
# Used by Claude Code SessionStart hook to inject handoff context automatically.
# This is the PRO CC version — reads "Session Handoff — Pro CC" + "Session Handoff — Shared"

osascript -e '
tell application "Notes"
    set targetFolder to folder "Claude 工作區" of account "iCloud"
    set allNotes to notes of targetFolder
    set output to ""

    -- Read private note
    repeat with aNote in allNotes
        if name of aNote is "Session Handoff — Pro CC" then
            set noteText to plaintext of aNote
            set modDate to modification date of aNote
            if length of noteText > 1800 then
                set noteText to text 1 thru 1800 of noteText & return & "[truncated]"
            end if
            set output to output & "Session Handoff — Pro CC (updated: " & modDate & "):" & return & noteText & return & return
            exit repeat
        end if
    end repeat

    -- Read shared note
    repeat with aNote in allNotes
        if name of aNote is "Session Handoff — Shared" then
            set noteText to plaintext of aNote
            set modDate to modification date of aNote
            if length of noteText > 1200 then
                set noteText to text 1 thru 1200 of noteText & return & "[truncated]"
            end if
            set output to output & "Session Handoff — Shared (updated: " & modDate & "):" & return & noteText
            exit repeat
        end if
    end repeat

    -- Fallback: try legacy "Session Handoff — Active"
    if output is "" then
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
        return "ℹ️ 沒有 Session Handoff 筆記"
    end if

    return output
end tell
'
