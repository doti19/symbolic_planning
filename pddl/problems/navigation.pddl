(define (problem navigation)
    (:domain building)

    (:objects Entrance Hallway Office Lab Meeting - room)


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
    )

    (:goal
        (and
            (robot-at Meeting)
        )
    )
)