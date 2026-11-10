
(define (problem human-handover)

    (:domain building)

    (:objects
        Entrance Hallway Office Lab Meeting - room
        book - item
        professor - person
        left right - gripper
    )

    (:init
        ;; Robot starting location
        (robot-at Entrance)

        ;; Building connections
        (connected Entrance Hallway)
        (connected Hallway Entrance)

        (connected Hallway Office)
        (connected Office Hallway)

        (connected Office Meeting)
        (connected Meeting Office)

        (connected Meeting Lab)
        (connected Lab Meeting)

        (connected Entrance Lab)
        (connected Lab Entrance)

        ;; Book location
        (item-at book Office)

        ;; Professor location
        (person-at professor Meeting)

        ;; Available grippers
        (gripper-free left)
        (gripper-free right)
    )

    (:goal
        (delivered-to book professor)
    )
)