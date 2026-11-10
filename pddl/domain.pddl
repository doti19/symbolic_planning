(define (domain building)
    (:requirements :strips :typing)

    (:types room item gripper table person door cabinet)

    (:predicates
    (robot-at ?r - room)
    (connected ?from ?to - room)
    
    (item-at ?o - item ?r - room)
    (gripper-free ?g - gripper)
    (holding ?o - item ?g - gripper)
    (table-at ?t - table ?r - room)
    (on-table ?o - item ?t - table)

    (person-at ?p - person ?r - room)
    (delivered-to ?o - item ?p - person)

    (door-between ?d - door ?from ?to - room)
    (door-closed ?d - door)

    (cabinet-at ?c - cabinet ?r - room)
    (cabinet-open ?c - cabinet)
    (in-cabinet ?o - item ?c - cabinet)
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


    (:action hand-over
        :parameters
            (?o - item ?p - person ?r - room ?g - gripper)

        :precondition(and
            (robot-at ?r)
            (person-at ?p ?r)
            (holding ?o ?g)
        )

        :effect(and
            (delivered-to ?o ?p)
            (gripper-free ?g)
            (not (holding ?o ?g))
        )
    )


    (:action open-door
        :parameters
            (?d - door ?from ?to - room)

        :precondition(and
            (robot-at ?from)
            (door-between ?d ?from ?to)
            (door-closed ?d)
        )

        :effect(and
            (not (door-closed ?d))
            (connected ?from ?to)
            (connected ?to ?from)
        )
    )

    (:action open-cabinet
        :parameters
            (?c - cabinet ?r - room)

        :precondition(and
            (robot-at ?r)
            (cabinet-at ?c ?r)
        )

        :effect
            (cabinet-open ?c)
    )


    (:action take-from-cabinet
        :parameters
            (?o - item ?c - cabinet ?r - room ?g - gripper)

        :precondition(and
            (robot-at ?r)
            (cabinet-at ?c ?r)
            (cabinet-open ?c)
            (in-cabinet ?o ?c)
            (gripper-free ?g)
        )

        :effect(and
            (holding ?o ?g)
            (not (in-cabinet ?o ?c))
            (not (gripper-free ?g))
        )
    )


)