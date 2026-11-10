
(define (problem door-navigation)

    (:domain building)

    (:objects
        Office Meeting - room
        office-door - door
    )

    (:init
        (robot-at Office)

        ;; Door exists in both directions
        (door-between office-door Office Meeting)
        (door-between office-door Meeting Office)

        ;; Initially closed
        (door-closed office-door)
    )

    (:goal
        (robot-at Meeting)
    )
)
