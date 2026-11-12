
(define (problem two-object-retrieval-unit)

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
      (= (distance entrance hallway) 1)
      (= (distance hallway entrance) 1)

      (= (distance hallway office) 1)
      (= (distance office hallway) 1)

      (= (distance office meeting) 1)
      (= (distance meeting office) 1)

      (= (distance entrance lab) 1)
      (= (distance lab entrance) 1)

      (= (distance lab meeting) 1)
      (= (distance meeting lab) 1)

      (= (distance hallway library) 1)
      (= (distance library hallway) 1)

      (= (distance library classroom) 1)
      (= (distance classroom library) 1)

      (= (distance classroom storage) 1)
      (= (distance storage classroom) 1)

      (= (distance storage meeting) 1)
      (= (distance meeting storage) 1)

      ;; Direct service-door shortcut
      (= (distance entrance storage) 1)
      (= (distance storage entrance) 1)

      ;; Expensive door opening
      (= (door-opening-cost service-door) 1)

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
