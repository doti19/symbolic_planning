
(define (problem cabinet-retrieval)

    (:domain building)

    (:objects
        Entrance Hallway Office Lab Meeting - room
        book - item
        left right - gripper
        office-cabinet - cabinet
        meeting-table - table
    )

    (:init
        ;; Robot starts at the entrance
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

        ;; Cabinet in the Office
        (cabinet-at office-cabinet Office)

        ;; Book is inside the cabinet
        (in-cabinet book office-cabinet)

        ;; Destination table
        (table-at meeting-table Meeting)

        ;; Both grippers available
        (gripper-free left)
        (gripper-free right)
    )

    (:goal
        (on-table book meeting-table)
    )
)
