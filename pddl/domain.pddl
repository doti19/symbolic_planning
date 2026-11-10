(define (domain building)
    (:requirements :strips :typing)

    (:types room item gripper table)

    (:predicates
    (robot-at ?r - room)
    (connected ?from ?to - room)
    (item-at ?o - item ?r - room)
    (gripper-free ?g - gripper)
    (holding ?o - item ?g - gripper)
    (table-at ?t - table ?r - room)
    (on-table ?o - item ?t - table)
    )

    (:action move
        :parameters (?from ?to - room)
        :precondition (and 
            (robot-at ?from)
            (connected ?from ?to)
        )
        :effect (and 
            (not (robot-at ?from))
            (robot-at ?to)
        )
    )

    (:action pick-up
        :parameters (?o - item ?r - room ?g - gripper)
        :precondition (and 
            (robot-at ?r)
            (item-at ?o ?r)
            (gripper-free ?g)
        )

        :effect (and 
            (holding ?o ?g)
            (not (item-at ?o ?r))
            (not (gripper-free ?g))
        )
    )

    (:action put-on-table
        :parameters (?o - item ?t - table ?r - room ?g - gripper)
        :precondition (and
            (robot-at ?r)
            (table-at ?t ?r)
            (holding ?o ?g)
        )

        :effect (and 
            (on-table ?o ?t)
            (gripper-free ?g)
            (not (holding ?o ?g))
        )
    
    )
)