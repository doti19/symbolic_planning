
(define (problem two-object-retrieval-weighted)

    (:domain building)

    (:objects
      entrance hallway office lab meeting
      library classroom storage - room
      service-door - door
      book laptop - item
      professor - person
      left right - gripper
    )

    (:init

      (robot-at entrance)

      ;; Existing eight-room connections
      (connected entrance hallway)
      (connected hallway entrance)

      (connected hallway office)
      (connected office hallway)

      (connected office meeting)
      (connected meeting office)

      (connected entrance lab)
      (connected lab entrance)

      (connected lab meeting)
      (connected meeting lab)

      (connected hallway library)
      (connected library hallway)

      (connected library classroom)
      (connected classroom library)

      (connected classroom storage)
      (connected storage classroom)

      (connected storage meeting)
      (connected meeting storage)

      ;; New shortcut door (initially closed)
      (door-between service-door entrance storage)
      (door-between service-door storage entrance)
      (door-closed service-door)

      ;; Initialize costs
      (= (total-cost) 0)

      ;; Original distances
      (= (distance entrance hallway) 3)
      (= (distance hallway entrance) 3)

      (= (distance hallway office) 3)
      (= (distance office hallway) 3)

      (= (distance office meeting) 3)
      (= (distance meeting office) 3)

      (= (distance entrance lab) 8)
      (= (distance lab entrance) 8)

      (= (distance lab meeting) 7)
      (= (distance meeting lab) 7)

      (= (distance hallway library) 2)
      (= (distance library hallway) 2)

      (= (distance library classroom) 2)
      (= (distance classroom library) 2)

      (= (distance classroom storage) 2)
      (= (distance storage classroom) 2)

      (= (distance storage meeting) 3)
      (= (distance meeting storage) 3)

      ;; Direct service-door shortcut
      (= (distance entrance storage) 2)
      (= (distance storage entrance) 2)

      ;; Expensive door opening
      (= (door-opening-cost service-door) 12)

      ;; these are new things initialized here from the door-detour problem
      (item-at book storage)
      (item-at laptop office)

      (person-at professor entrance)

      (gripper-free left)
      (gripper-free right)
    )

    (:goal
      (and
        (delivered-to book professor)
        (delivered-to laptop professor)
      )
    )

    (:metric minimize (total-cost))
)
