import os
import datetime
from provenancetoolbox import notebook

import pytest

import cloudvolume as cv


def basic_note_tests(testcloudvolume, note):
    'Basic tests to run for every note type'
    newnotes = notebook.parsenotes(testcloudvolume)
    assert newnotes[-1].content == note.content
    assert newnotes[-1].note_type == note.note_type
    assert (newnotes[-1].timestamp - note.timestamp
            < datetime.timedelta(seconds=1))


def test_addnotes(testcloudvolume):
    'Tests for the generic addnotes function'
    origlen = len(notebook.parsenotes(testcloudvolume))
    timestamp = datetime.datetime.now()

    # If we add a note, can we retrieve it?
    firstcontent = 'First note'
    notebook.addnote(testcloudvolume, notebook.NoteType.GENERIC, firstcontent)
    desirednote = notebook.Note(timestamp, notebook.NoteType.GENERIC,
                                firstcontent)

    newnotes = notebook.parsenotes(testcloudvolume)
    assert len(newnotes) == origlen + 1

    basic_note_tests(testcloudvolume, desirednote)


def test_addmotivation(testcloudvolume):
    'Tests for adding motivation notes'
    motivation = 'We did it because we must'
    timestamp = datetime.datetime.now()

    notebook.addmotivation(testcloudvolume, motivation)
    desirednote = notebook.Note(timestamp, notebook.NoteType.MOTIVATION,
                                motivation)
    basic_note_tests(testcloudvolume, desirednote)


def test_addresult(testcloudvolume):
    'Tests for adding result notes'
    result = 'We did the thing'
    timestamp = datetime.datetime.now()

    notebook.addresult(testcloudvolume, result)
    desirednote = notebook.Note(timestamp, notebook.NoteType.RESULT, result)

    basic_note_tests(testcloudvolume, desirednote)
