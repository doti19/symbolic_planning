;Header and description

(define (problem object-delivery)

    (:domain building)

    (:objects
        Entrance Hallway Office Lab Meeting - room
        book - item
        left right - gripper
        meeting-table - table
    )

    (:init
        (robot-at Entrance)

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

        (item-at book Office)
        (table-at meeting-table Meeting)

        (gripper-free left)
        (gripper-free right)
    )

    (:goal
        (on-table book meeting-table)
    )
)