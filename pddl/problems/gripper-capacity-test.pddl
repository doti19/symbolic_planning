
(define (problem two-object-transport)

    (:domain building)

    (:objects
        Entrance Hallway Office Lab Meeting - room
        book laptop cup - item
        left right - gripper
        meeting-table - table
    )

    (:init
        ;; Initial robot location
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

        ;; Both objects are in the Office
        (item-at book Office)
        (item-at laptop Office)

        ;; Destination table
        (table-at meeting-table Meeting)

        ;; Both grippers are initially empty
        (gripper-free left)
        (gripper-free right)
    )

    
    (:goal
    (and
        (holding book left)
        (holding laptop right)
        (holding cup left)
    )
    )
)
