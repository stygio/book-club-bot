from pyrankvote import Candidate, Ballot, instant_runoff_voting
import prettytable as pt

import customTypes as types


def performVote(userVotes: dict[int, list[int]], submissions: dict[int, types.BookVolume | None]) -> int:
    # Map of submissionId -> Candidate
    submissionCandidates = { submissionId: Candidate(submissionId) for submissionId in submissions.keys() }
    # Map of userId -> ranked list of Candidates
    userVotesForCandidates: dict[str, list[Candidate]] = {}
    for userId, votes in userVotes.items():
        userVotesForCandidates[userId] = [submissionCandidates[vote] for vote in votes]
    # Preparing ballots based on user ranked lists of candidates
    ballots = [Ballot(ranked_candidates = votes) for votes in userVotesForCandidates.values()]

    result = instant_runoff_voting(candidates = [candidate for candidate in submissionCandidates.values()], ballots = ballots)
    winningCandidate = result.get_winners()[0]
    candidateToSubmissionId = { candidate: submissionId for submissionId, candidate in submissionCandidates.items() }
    winningSubmissionId = candidateToSubmissionId[winningCandidate]

    return winningSubmissionId

def userVoteRankForSubmission(submissionId: int, votes: list[int]):
    if not submissionId in votes:
        return ''
    voteIndex = votes.index(submissionId)
    return str(voteIndex + 1)

def drawVoteTable(userVotes: dict[str, list[int]], submissions: dict[int, types.BookVolume | None], userNames: dict[int, str]) -> str:
    # Build table corresponding to how each user voted for each submission
    table: list[list[str]] = []
    for uIdx, votes in enumerate(userVotes.values()):
        table.append([])
        for submissionId in submissions.keys():
            table[uIdx].append(userVoteRankForSubmission(submissionId, votes))
    
    row = ['']
    row.extend([str(submissionId) for submissionId in submissions.keys()])
    voteTable = pt.PrettyTable(row)
    for uIdx, userSubmissionVotes in enumerate(table):
        userId = list(userVotes.keys())[uIdx]
        row = [userNames[userId]]
        row.extend(userSubmissionVotes)
        voteTable.add_row(row)

    print(voteTable)
    return f'<pre>{voteTable}</pre>'

    