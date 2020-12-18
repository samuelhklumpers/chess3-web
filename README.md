3rd incarnation of the chess project.


How does this work?

Part 1: How do I run it?
1. install python
2. pip install -r requirements.txt 
   (unless you already have numpy)
3. python game.py

Part 2: How do I add a (simple) piece?
1. Take your board string 

> "wa8Th8Tb8Pg8Pc8Lf8Ld8De8Ka7pb7pc7pd7pe7pf7pg7ph7p;ba1Th1Tb1Pg1Pc1Lf1Ld1De1Ka2pb2pc2pd2pe2pf2pg2ph2p"

   and replace the relevant positions with your pieces, format is colour1piece11piece12...;colour2...
   where a piece is a position (a-h1-8) followed by its appearance (any ascii character)
   
2. Go to chess_rules.py, copy one of the existing move rules, replace the "K" in this line
> if piece.shape == "K":
   
   with the appearance you chose, and fill in your own logic for deciding the possibility of a move.
   At the end
> return [(self.eout, args)]
   
   to confirm the move.
   
3. Go to game.py, and either copy play_chess or edit it directly, and inject your new rule into the list of piece rules in this section

>   ruleset = Ruleset(chess)
>
>   move_rules = [
>       [IdMoveRule], [MoveTurnRule], [MovePlayerRule], [FriendlyFireRule],
>       [PawnSingleRule, PawnDoubleRule, PawnTakeRule, PawnEnPassantRule, KnightRule, BishopRule, RookRule,
>        QueenRule, KingRule, CastleRule]
>   ]
    
Part 3: How do I add a slightly more complex piece or implement other effects?
1. Make sure you understand how the Ruleset class works and propagates, and why it is not recommended to return an effect of the type you are listening for, unless
   you know how to terminate the recursion you otherwise create.
   
2. Most things that can happen in a chess game already generate their consequences, to create a new effect, you typically make your rule listen for one of these,
   and then process its arguments to decide if and what your rule should do.
   Rules are free to generate side effects on any member of the passed Game instance (tampering with the ruleset is still not recommended),
   or return new consequences for other rules.
   
3. Some things can be directly implemented (e.g. take all pieces adjacent to a piece after it is taken), while others might require you to modify the existing structures of
   the game (e.g. use custom images for drawing)
